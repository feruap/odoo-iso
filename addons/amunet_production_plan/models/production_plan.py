# -*- coding: utf-8 -*-
"""Plan de produccion sugerido: demanda -> oferta -> restriccion de materia prima."""
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round

_logger = logging.getLogger(__name__)


class ProductionPlan(models.Model):
    _name = 'amunet.production.plan'
    _description = 'Plan de produccion sugerido'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Folio', default='Nuevo', readonly=True, copy=False, required=True)
    company_id = fields.Many2one(
        'res.company', string='Compania', required=True,
        default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('computed', 'Calculado'),
        ('done', 'Ordenes generadas'),
    ], default='draft', string='Estado', tracking=True)

    demand_source = fields.Selection([
        ('woo', 'Tendencia WooCommerce (piezas vendidas)'),
        ('sale', 'Pedidos de venta de Odoo'),
        ('stock', 'Salidas de almacen a cliente'),
    ], string='Fuente de demanda', default='stock', required=True, tracking=True,
        help='De donde se lee el historico. Ninguna opcion trae importes, solo cantidades.')

    date_from = fields.Date(
        string='Historico desde', required=True,
        default=lambda self: fields.Date.context_today(self) - timedelta(days=90))
    date_to = fields.Date(
        string='Historico hasta', required=True,
        default=lambda self: fields.Date.context_today(self))
    horizon_days = fields.Integer(
        string='Dias a cubrir', default=30, required=True,
        help='Cuantos dias de demanda debe cubrir la produccion sugerida.')
    safety_days = fields.Integer(
        string='Stock de seguridad (dias)', default=15,
        help='Colchon adicional expresado en dias de demanda.')

    categ_ids = fields.Many2many(
        'product.category', string='Categorias',
        help='Vacio = todas las categorias con demanda en la ventana.')
    only_with_bom = fields.Boolean(
        string='Solo productos con BoM', default=True,
        help='Sin BoM no se puede fabricar ni validar materia prima.')

    line_ids = fields.One2many('amunet.production.plan.line', 'plan_id', string='Lineas')
    shortage_ids = fields.One2many(
        'amunet.production.plan.shortage', 'plan_id', string='Faltantes de materia prima')

    line_count = fields.Integer(compute='_compute_counts')
    to_produce_count = fields.Integer(compute='_compute_counts')
    blocked_count = fields.Integer(compute='_compute_counts')
    shortage_count = fields.Integer(compute='_compute_counts')

    @api.depends('line_ids.qty_to_produce', 'line_ids.qty_suggested', 'shortage_ids')
    def _compute_counts(self):
        for plan in self:
            lines = plan.line_ids
            plan.line_count = len(lines)
            plan.to_produce_count = len(lines.filtered(lambda l: l.qty_to_produce > 0))
            plan.blocked_count = len(lines.filtered(
                lambda l: l.qty_suggested > 0 and l.qty_to_produce <= 0))
            plan.shortage_count = len(plan.shortage_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.production.plan') or 'PLAN/%s' % fields.Date.context_today(self)
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Demanda
    # ------------------------------------------------------------------
    def _window_days(self):
        self.ensure_one()
        return max((self.date_to - self.date_from).days, 1)

    def _demand_from_woo(self):
        """{product_id: piezas} desde amunet.woo.sales.trend (sin importes)."""
        Trend = self.env.get('amunet.woo.sales.trend')
        if Trend is None:
            return {}
        rows = self.env['amunet.woo.sales.trend'].sudo().search([
            ('sale_date', '>=', self.date_from),
            ('sale_date', '<=', self.date_to),
        ])
        demand = {}
        for row in rows:
            product = row.product_id or row.product_tmpl_id.product_variant_id
            if not product:
                continue
            demand[product.id] = demand.get(product.id, 0.0) + (row.piece_qty or 0.0)
        return demand

    def _demand_from_sale(self):
        if 'sale.order.line' not in self.env:
            raise UserError(_('El modulo de Ventas no esta instalado en esta base.'))
        lines = self.env['sale.order.line'].sudo().search([
            ('order_id.date_order', '>=', fields.Datetime.to_datetime(self.date_from)),
            ('order_id.date_order', '<=', fields.Datetime.to_datetime(self.date_to)),
            ('order_id.state', 'in', ('sale', 'done')),
            ('product_id.type', '!=', 'service'),
        ])
        demand = {}
        for line in lines:
            demand[line.product_id.id] = demand.get(line.product_id.id, 0.0) + line.product_uom_qty
        return demand

    def _demand_from_stock(self):
        """Salidas reales a cliente. Funciona sin Ventas y sin Woo."""
        moves = self.env['stock.move'].sudo().search([
            ('state', '=', 'done'),
            ('date', '>=', fields.Datetime.to_datetime(self.date_from)),
            ('date', '<=', fields.Datetime.to_datetime(self.date_to)),
            ('location_dest_id.usage', 'in', ('customer', 'production')),
            ('location_id.usage', '=', 'internal'),
            ('company_id', '=', self.company_id.id),
        ])
        demand = {}
        for move in moves:
            demand[move.product_id.id] = demand.get(move.product_id.id, 0.0) + move.quantity
        return demand

    def _get_demand(self):
        self.ensure_one()
        if self.demand_source == 'woo':
            return self._demand_from_woo()
        if self.demand_source == 'sale':
            return self._demand_from_sale()
        return self._demand_from_stock()

    # ------------------------------------------------------------------
    # Calculo
    # ------------------------------------------------------------------
    def action_compute(self):
        self.ensure_one()
        self.line_ids.unlink()
        self.shortage_ids.unlink()

        demand = self._get_demand()
        if not demand:
            raise UserError(_(
                'No hay demanda en la ventana %(a)s a %(b)s con la fuente elegida. '
                'Prueba con otra fuente o amplia el periodo.',
                a=self.date_from, b=self.date_to))

        days = self._window_days()
        products = self.env['product.product'].browse(list(demand)).exists()
        if self.categ_ids:
            products = products.filtered(lambda p: p.categ_id in self.categ_ids)

        Line = self.env['amunet.production.plan.line']
        shortages = {}
        for product in products:
            qty_hist = demand.get(product.id, 0.0)
            if qty_hist <= 0:
                continue
            bom = self.env['mrp.bom']._bom_find(
                product, company_id=self.company_id.id).get(product)
            if self.only_with_bom and not bom:
                continue

            daily = qty_hist / days
            need = daily * (self.horizon_days + self.safety_days)
            on_hand = product.with_company(self.company_id).free_qty
            wip = self._wip_qty(product)
            suggested = max(0.0, need - on_hand - wip)
            suggested = float_round(suggested, precision_rounding=1.0, rounding_method='UP')

            coverage, missing = self._bom_coverage(product, bom, suggested)
            to_produce = float_round(
                suggested * coverage, precision_rounding=1.0, rounding_method='DOWN')

            line = Line.create({
                'plan_id': self.id,
                'product_id': product.id,
                'bom_id': bom.id if bom else False,
                'qty_history': qty_hist,
                'qty_daily': daily,
                'qty_need': need,
                'qty_on_hand': on_hand,
                'qty_released': self._released_qty(product),
                'qty_wip': wip,
                'qty_suggested': suggested,
                'mp_coverage': coverage * 100.0,
                'qty_to_produce': to_produce,
                'blocking_note': ', '.join(missing.keys()) if missing else '',
            })
            for comp_id, data in missing.items():
                key = data['product_id']
                acc = shortages.setdefault(key, {'required': 0.0, 'available': data['available']})
                acc['required'] += data['required']
                acc.setdefault('lines', []).append(line.id)

        Shortage = self.env['amunet.production.plan.shortage']
        for product_id, data in shortages.items():
            Shortage.create({
                'plan_id': self.id,
                'product_id': product_id,
                'qty_required': data['required'],
                'qty_available': data['available'],
            })

        self.state = 'computed'
        self.message_post(body=_(
            'Plan calculado: %(n)s productos con demanda, %(p)s con produccion posible, '
            '%(b)s bloqueados por materia prima.',
            n=len(self.line_ids), p=self.to_produce_count, b=self.blocked_count))
        return True

    def _wip_qty(self, product):
        mos = self.env['mrp.production'].sudo().search([
            ('product_id', '=', product.id),
            ('state', 'not in', ('done', 'cancel')),
            ('company_id', '=', self.company_id.id),
        ])
        return sum(mos.mapped('product_qty'))

    def _released_qty(self, product):
        """Piezas en lotes liberados por Calidad, si amunet_lot esta instalado."""
        Quant = self.env['stock.quant'].sudo()
        if 'amunet_lot_release_state' not in self.env['stock.lot']._fields:
            return 0.0
        quants = Quant.search([
            ('product_id', '=', product.id),
            ('location_id.usage', '=', 'internal'),
            ('company_id', '=', self.company_id.id),
        ])
        return sum(
            q.quantity - q.reserved_quantity for q in quants
            if q.lot_id and q.lot_id.amunet_lot_release_state == 'released')

    @staticmethod
    def _is_stock_tracked(product):
        if 'is_storable' in product._fields:
            return bool(product.is_storable)
        return product.type == 'product'

    def _bom_coverage(self, product, bom, qty):
        """Devuelve (cobertura 0..1, {nombre_componente: datos}) explotando la BoM."""
        if not bom or qty <= 0:
            return (1.0 if qty <= 0 else 0.0 if self.only_with_bom else 1.0), {}
        try:
            _boms, bom_lines = bom.explode(product, qty / (bom.product_qty or 1.0))
        except Exception as exc:  # pragma: no cover - defensivo
            _logger.warning('No se pudo explotar la BoM de %s: %s', product.display_name, exc)
            return 0.0, {}

        coverage = 1.0
        missing = {}
        for bom_line, line_data in bom_lines:
            component = bom_line.product_id
            required = line_data.get('qty') or line_data.get('quantity') or 0.0
            if required <= 0 or component.type == 'service':
                continue
            if not self._is_stock_tracked(component):
                # Un componente que Odoo no inventaria (consumible puro) no puede
                # bloquear el plan: su existencia siempre seria cero.
                continue
            available = component.with_company(self.company_id).free_qty
            ratio = 1.0 if required <= 0 else min(1.0, available / required)
            if float_compare(available, required, precision_digits=3) < 0:
                missing[component.display_name] = {
                    'product_id': component.id,
                    'required': required,
                    'available': available,
                }
            coverage = min(coverage, ratio)
        return max(coverage, 0.0), missing

    # ------------------------------------------------------------------
    # Ordenes de fabricacion
    # ------------------------------------------------------------------
    def action_create_mos(self):
        self.ensure_one()
        lines = self.line_ids.filtered(lambda l: l.qty_to_produce > 0 and not l.production_id)
        if not lines:
            raise UserError(_('No hay lineas con cantidad a producir pendientes de orden.'))
        Production = self.env['mrp.production']
        created = Production.browse()
        for line in lines:
            mo = Production.create({
                'product_id': line.product_id.id,
                'product_qty': line.qty_to_produce,
                'product_uom_id': line.product_id.uom_id.id,
                'bom_id': line.bom_id.id or False,
                'company_id': self.company_id.id,
                'origin': self.name,
            })
            line.production_id = mo.id
            created |= mo
        self.state = 'done'
        self.message_post(body=_('Se crearon %s ordenes de fabricacion en borrador.', len(created)))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ordenes generadas'),
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created.ids)],
        }

    def action_view_shortages(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Faltantes de materia prima'),
            'res_model': 'amunet.production.plan.shortage',
            'view_mode': 'list',
            'domain': [('plan_id', '=', self.id)],
        }


class ProductionPlanLine(models.Model):
    _name = 'amunet.production.plan.line'
    _description = 'Linea de plan de produccion'
    _order = 'qty_suggested desc, id'

    plan_id = fields.Many2one('amunet.production.plan', required=True, ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    categ_id = fields.Many2one(related='product_id.categ_id', string='Categoria', store=True)
    bom_id = fields.Many2one('mrp.bom', string='Lista de materiales')

    qty_history = fields.Float(string='Vendido en la ventana', digits='Product Unit of Measure')
    qty_daily = fields.Float(string='Demanda diaria', digits='Product Unit of Measure')
    qty_need = fields.Float(string='Necesidad del horizonte', digits='Product Unit of Measure')
    qty_on_hand = fields.Float(string='Existencia libre', digits='Product Unit of Measure')
    qty_released = fields.Float(string='Existencia liberada', digits='Product Unit of Measure')
    qty_wip = fields.Float(string='En produccion', digits='Product Unit of Measure')
    qty_suggested = fields.Float(string='Sugerido', digits='Product Unit of Measure')
    mp_coverage = fields.Float(string='Cobertura MP (%)')
    qty_to_produce = fields.Float(string='A producir', digits='Product Unit of Measure')
    blocking_note = fields.Char(string='Materia prima que falta')
    production_id = fields.Many2one('mrp.production', string='Orden creada', readonly=True)

    status = fields.Selection([
        ('ok', 'Se puede producir'),
        ('partial', 'Alcanza parcial'),
        ('blocked', 'Bloqueado por materia prima'),
        ('none', 'Sin necesidad'),
    ], compute='_compute_status', store=True, string='Situacion')

    @api.depends('qty_suggested', 'qty_to_produce', 'mp_coverage')
    def _compute_status(self):
        for line in self:
            if line.qty_suggested <= 0:
                line.status = 'none'
            elif line.qty_to_produce <= 0:
                line.status = 'blocked'
            elif line.qty_to_produce < line.qty_suggested:
                line.status = 'partial'
            else:
                line.status = 'ok'


class ProductionPlanShortage(models.Model):
    _name = 'amunet.production.plan.shortage'
    _description = 'Faltante de materia prima del plan'
    _order = 'qty_missing desc, id'

    plan_id = fields.Many2one('amunet.production.plan', required=True, ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product', string='Materia prima', required=True)
    qty_required = fields.Float(string='Requerido', digits='Product Unit of Measure')
    qty_available = fields.Float(string='Disponible', digits='Product Unit of Measure')
    qty_missing = fields.Float(string='Faltante', compute='_compute_missing', store=True,
                               digits='Product Unit of Measure')
    seller_id = fields.Many2one(
        'res.partner', string='Proveedor habitual', compute='_compute_seller', store=False)

    def _compute_seller(self):
        for rec in self:
            seller = rec.product_id.seller_ids[:1]
            rec.seller_id = seller.partner_id.id if seller else False

    @api.depends('qty_required', 'qty_available')
    def _compute_missing(self):
        for rec in self:
            rec.qty_missing = max(0.0, rec.qty_required - rec.qty_available)
