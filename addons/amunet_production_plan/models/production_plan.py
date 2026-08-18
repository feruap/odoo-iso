# -*- coding: utf-8 -*-
"""Plan de produccion sugerido: demanda -> oferta -> restriccion de materia prima."""
import logging
from datetime import datetime, time, timedelta

import pytz

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
        string='Solo productos con BoM', default=False,
        help='Si se activa, ignora los productos de compra-reventa (sin BoM).')
    stock_basis = fields.Selection([
        ('released', 'Solo existencia liberada por Calidad'),
        ('free', 'Toda la existencia libre'),
    ], string='Que cuenta como disponible', default='released', required=True,
        help='Lo que no ha liberado Calidad no es vendible. Con "liberada" el plan '
             'no lo cuenta como oferta, pero lo reporta aparte para que se vea que '
             'el cuello de botella es liberacion, no compra ni produccion.')

    mp_basis = fields.Selection([
        ('free', 'Toda la existencia libre'),
        ('released', 'Solo materia prima liberada por Calidad'),
    ], string='Materia prima disponible', default='free', required=True,
        help='Hoy Calidad libera lotes de producto terminado, no de materia prima: '
             'con "liberada" el plan no podria fabricar nada. Cambialo a "liberada" '
             'el dia que se empiecen a liberar tambien los lotes de insumos.')

    line_ids = fields.One2many('amunet.production.plan.line', 'plan_id', string='Lineas')
    shortage_ids = fields.One2many(
        'amunet.production.plan.shortage', 'plan_id', string='Faltantes de materia prima')

    line_count = fields.Integer(compute='_compute_counts')
    to_produce_count = fields.Integer(compute='_compute_counts')
    to_buy_count = fields.Integer(compute='_compute_counts')
    blocked_count = fields.Integer(compute='_compute_counts')
    pending_qc_count = fields.Integer(compute='_compute_counts')
    shortage_count = fields.Integer(compute='_compute_counts')
    unknown_count = fields.Integer(compute='_compute_counts')

    @api.depends('line_ids.qty_to_produce', 'line_ids.qty_to_buy',
                 'line_ids.qty_suggested', 'line_ids.qty_pending_qc', 'shortage_ids')
    def _compute_counts(self):
        for plan in self:
            lines = plan.line_ids
            plan.line_count = len(lines)
            plan.to_produce_count = len(lines.filtered(lambda l: l.qty_to_produce > 0))
            plan.to_buy_count = len(lines.filtered(lambda l: l.qty_to_buy > 0))
            plan.blocked_count = len(lines.filtered(
                lambda l: l.supply_mode == 'manufacture'
                and l.qty_suggested > 0 and l.qty_to_produce <= 0))
            plan.pending_qc_count = len(lines.filtered(lambda l: l.qty_pending_qc > 0))
            plan.shortage_count = len(plan.shortage_ids)
            plan.unknown_count = len(lines.filtered(
                lambda l: l.supply_mode == 'unknown' and l.qty_suggested > 0))

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
        """Dias de la ventana contando ambos extremos (inclusiva)."""
        self.ensure_one()
        return max((self.date_to - self.date_from).days + 1, 1)

    def _tz(self):
        return pytz.timezone(self.env.user.tz or 'America/Mexico_City')

    def _to_utc(self, fecha, fin=False):
        """Odoo guarda las fechas y horas en UTC. Tomar la medianoche UTC como
        limite corre la ventana varias horas en Mexico, asi que se convierte la
        medianoche LOCAL (o el final del dia local) a UTC."""
        tz = self._tz()
        local = tz.localize(datetime.combine(fecha, time.max if fin else time.min))
        return local.astimezone(pytz.UTC).replace(tzinfo=None)

    def _dt_from(self):
        return self._to_utc(self.date_from)

    def _dt_to(self):
        """Fin del ultimo dia: si no, se pierden ~24 h de historico."""
        return self._to_utc(self.date_to, fin=True)

    def _demand_from_woo(self):
        """{product_id: piezas} desde amunet.woo.sales.trend (sin importes)."""
        Trend = self.env.get('amunet.woo.sales.trend')
        if Trend is None:
            return {}
        dominio = [
            ('sale_date', '>=', self.date_from),
            ('sale_date', '<=', self.date_to),
        ]
        if 'company_id' in self.env['amunet.woo.sales.trend']._fields:
            dominio.append(('company_id', 'in', (self.company_id.id, False)))
        rows = self.env['amunet.woo.sales.trend'].sudo().search(dominio)
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
            ('order_id.date_order', '>=', self._dt_from()),
            ('order_id.date_order', '<=', self._dt_to()),
            ('order_id.state', 'in', ('sale', 'done')),
            ('order_id.company_id', '=', self.company_id.id),
            ('product_id.type', '!=', 'service'),
        ])
        demand = {}
        for line in lines:
            producto = line.product_id
            qty = line.product_uom_qty
            # La linea puede estar en cajas y la produccion se mide en piezas.
            uom = getattr(line, 'product_uom_id', False) or getattr(line, 'product_uom', False)
            if uom and producto.uom_id and uom != producto.uom_id:
                qty = uom._compute_quantity(qty, producto.uom_id)
            demand[producto.id] = demand.get(producto.id, 0.0) + qty
        return demand

    def _demand_from_stock(self):
        """Salidas reales a cliente. Funciona sin Ventas y sin Woo."""
        # Solo salidas a cliente. El consumo hacia 'production' NO es demanda:
        # ya se contabiliza al explotar la BoM del producto terminado y contarlo
        # aqui inflaria la necesidad de materia prima al doble.
        moves = self.env['stock.move'].sudo().search([
            ('state', '=', 'done'),
            ('date', '>=', self._dt_from()),
            ('date', '<=', self._dt_to()),
            ('location_dest_id.usage', '=', 'customer'),
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
    def _lock(self):
        """Candado de fila: evita que dos llamadas concurrentes (RPC, doble
        clic, cron) recalculen o generen ordenes sobre el mismo plan."""
        self.ensure_one()
        try:
            self.env.cr.execute(
                'SELECT id FROM amunet_production_plan WHERE id = %s FOR UPDATE NOWAIT',
                (self.id,))
        except Exception:
            raise UserError(_(
                'Otro usuario esta trabajando sobre este plan en este momento. '
                'Vuelve a intentarlo en unos segundos.'))

    def action_compute(self):
        self.ensure_one()
        self._lock()
        if self.state == 'done':
            raise UserError(_(
                'Este plan ya genero ordenes de fabricacion. Duplica el plan '
                'en lugar de recalcularlo: recalcular borraria la trazabilidad.'))
        con_mo = self.line_ids.filtered(lambda l: l.production_id)
        if con_mo:
            raise UserError(_(
                'Hay %s lineas con orden de fabricacion ya creada. No se puede '
                'recalcular sin perder el enlace.', len(con_mo)))
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
        # Materia prima compartida: un mismo reactivo alimenta varias pruebas.
        # mp_pool guarda lo que va quedando conforme se aparta para cada linea;
        # mp_total guarda la existencia libre original para el reporte.
        mp_pool, mp_total = {}, {}
        # Lo que el plan completo pediria de cada materia prima, para que el
        # reporte de faltantes no compare la necesidad de una sola linea contra
        # la existencia total.
        requerido_total = {}
        # Se atiende primero al de mayor demanda historica: si la MP no alcanza,
        # que se la lleve el producto que mas se vende, no el primero por id.
        products = products.sorted(lambda p: demand.get(p.id, 0.0), reverse=True)
        for product in products:
            qty_hist = demand.get(product.id, 0.0)
            if qty_hist <= 0:
                continue
            bom = self.env['mrp.bom']._bom_find(
                product, company_id=self.company_id.id).get(product)
            if self.only_with_bom and not bom:
                continue
            if bom:
                supply_mode = 'manufacture'
            elif product.purchase_ok:
                supply_mode = 'buy'
            else:
                supply_mode = 'unknown'

            daily = qty_hist / days
            need = daily * (self.horizon_days + self.safety_days)
            free = self._en_compania(product).free_qty
            # La liberacion por Calidad se lleva por lote. Un producto que no se
            # rastrea por lote nunca tendria existencia liberada y el plan pediria
            # fabricar de nuevo todo lo que ya hay en almacen.
            aplica_liberacion = self._release_applies(product)
            released = self._released_qty(product) if aplica_liberacion else free
            pending_qc = max(0.0, free - released) if aplica_liberacion else 0.0
            on_hand = released if (self.stock_basis == 'released'
                                   and aplica_liberacion) else free
            wip = self._wip_qty(product)
            entrante = self._incoming_qty(product)
            suggested = max(0.0, need - on_hand - wip - entrante)
            suggested = float_round(suggested, precision_rounding=1.0, rounding_method='UP')

            to_produce = to_buy = 0.0
            coverage, missing, needs = 1.0, {}, {}
            error_bom = False
            if supply_mode == 'manufacture':
                coverage, missing, needs = self._bom_coverage(
                    product, bom, suggested, mp_pool, mp_total)
                error_bom = needs is None
                to_produce = float_round(
                    suggested * coverage, precision_rounding=1.0, rounding_method='DOWN')
                # Se aparta la materia prima de lo que REALMENTE se va a fabricar.
                # Apartarla en proporcion a la cobertura dejaba comprometida MP de
                # una fabricacion fraccionaria que al redondear hacia abajo nunca
                # ocurre, y bloqueaba injustamente a los productos siguientes.
                if needs:
                    ratio = (to_produce / suggested) if suggested > 0 else 0.0
                    self._bom_consume(needs, mp_pool, ratio)
                    for comp_id, data in needs.items():
                        acc = requerido_total.setdefault(comp_id, 0.0)
                        requerido_total[comp_id] = acc + data['required']
            elif supply_mode == 'buy':
                # Compra-reventa: no hay BoM que explotar, la restriccion es el
                # proveedor. Se sugiere comprar y Calidad tendra que liberarlo.
                to_buy = suggested

            note = ', '.join(d['name'] for d in missing.values()) if missing else ''
            if error_bom:
                note = _('No se pudo explotar la lista de materiales: revisala '
                         'antes de confiar en esta linea')
            if supply_mode == 'unknown' and suggested > 0:
                aviso_u = _('Sin lista de materiales y sin marcar como comprable: '
                            'el plan no puede proponer nada')
                note = '%s | %s' % (note, aviso_u) if note else aviso_u
            if pending_qc > 0:
                aviso = _('%(n)s piezas esperando liberacion de Calidad') % {
                    'n': int(pending_qc)}
                note = '%s | %s' % (note, aviso) if note else aviso

            line = Line.create({
                'plan_id': self.id,
                'product_id': product.id,
                'bom_id': bom.id if bom else False,
                'supply_mode': supply_mode,
                'qty_history': qty_hist,
                'qty_daily': daily,
                'qty_need': need,
                'qty_on_hand': on_hand,
                'qty_free': free,
                'qty_released': released,
                'qty_pending_qc': pending_qc,
                'qty_wip': wip,
                'qty_incoming': entrante,
                'qty_suggested': suggested,
                'mp_coverage': coverage * 100.0,
                'qty_to_produce': to_produce,
                'qty_to_buy': to_buy,
                'blocking_note': note,
            })
        Shortage = self.env['amunet.production.plan.shortage']
        for comp_id, requerido in requerido_total.items():
            disponible = mp_total.get(comp_id, 0.0)
            if float_compare(disponible, requerido, precision_digits=3) >= 0:
                continue
            Shortage.create({
                'plan_id': self.id,
                'product_id': comp_id,
                'qty_required': requerido,
                'qty_available': disponible,
            })

        self.state = 'computed'
        self.message_post(body=_(
            'Plan calculado: %(n)s productos con demanda, %(p)s a producir, '
            '%(c)s a comprar, %(b)s bloqueados por materia prima, '
            '%(u)s sin BoM y sin marcar como comprables.',
            n=len(self.line_ids), p=self.to_produce_count,
            c=self.to_buy_count, b=self.blocked_count, u=self.unknown_count))
        return True

    def _wip_qty(self, product):
        mos = self.env['mrp.production'].sudo().search([
            ('product_id', '=', product.id),
            ('state', 'not in', ('done', 'cancel')),
            ('company_id', '=', self.company_id.id),
        ])
        pendiente = 0.0
        for mo in mos:
            hecho = mo.qty_produced if 'qty_produced' in mo._fields else 0.0
            pendiente += max(0.0, (mo.product_qty or 0.0) - (hecho or 0.0))
        return pendiente

    def _tracks_release(self):
        return 'amunet_lot_release_state' in self.env['stock.lot']._fields

    def _en_compania(self, records):
        """with_company() no basta: free_qty se calcula sobre allowed_company_ids,
        que puede arrastrar otras companias del contexto y sumar stock ajeno."""
        return records.with_company(self.company_id).with_context(
            allowed_company_ids=self.company_id.ids)

    def _release_applies(self, product):
        """La liberacion de Calidad solo tiene sentido si el producto lleva lote."""
        return self._tracks_release() and product.tracking != 'none'

    def _available_qty(self, product, componente=False):
        """Existencia utilizable segun la base elegida.

        El producto terminado y la materia prima llevan bases distintas a
        proposito: hoy Calidad libera lotes de producto terminado, no de insumos.
        Si se exigiera lote liberado tambien en la materia prima, el plan no
        propondria fabricar nada. `mp_basis` deja activarlo cuando la practica
        cambie.
        """
        libre = self._en_compania(product).free_qty
        base = self.mp_basis if componente else self.stock_basis
        if base == 'released' and self._release_applies(product):
            return min(libre, self._released_qty(product))
        return libre

    def _incoming_qty(self, product):
        """Piezas ya compradas y aun no recibidas.

        Sin esto el plan vuelve a pedir lo que ya viene en camino en una orden de
        compra confirmada. Solo cuenta lo que entra desde un proveedor: lo que
        entra desde produccion ya se mide en _wip_qty.
        """
        moves = self.env['stock.move'].sudo().search([
            ('product_id', '=', product.id),
            ('state', 'not in', ('done', 'cancel', 'draft')),
            ('location_id.usage', '=', 'supplier'),
            ('location_dest_id.usage', '=', 'internal'),
            ('company_id', '=', self.company_id.id),
        ])
        return sum(moves.mapped('product_qty'))

    def _released_qty(self, product):
        """Piezas en lotes liberados por Calidad, si amunet_lot esta instalado."""
        Quant = self.env['stock.quant'].sudo()
        if not self._tracks_release():
            return 0.0
        quants = Quant.search([
            ('product_id', '=', product.id),
            ('location_id.usage', '=', 'internal'),
            ('company_id', '=', self.company_id.id),
        ])
        lotes_liberados = quants.mapped('lot_id').filtered(
            lambda l: l.amunet_lot_release_state == 'released')
        released_total = sum(
            q.quantity for q in quants if q.lot_id and q.lot_id in lotes_liberados)
        if not released_total:
            return 0.0
        # En Odoo 19 las reservas viven en stock.move.line, no en el quant. Se
        # descuenta UNICAMENTE la reserva que pesa sobre lotes liberados: restar
        # la reserva global castigaria el stock liberado por lotes en cuarentena.
        product = self._en_compania(product)
        reservas = self.env['stock.move.line'].sudo().search([
            ('product_id', '=', product.id),
            ('lot_id', 'in', lotes_liberados.ids),
            ('state', 'not in', ('done', 'cancel')),
            ('location_id.usage', '=', 'internal'),
            ('company_id', '=', self.company_id.id),
        ])
        campo = 'quantity_product_uom' if 'quantity_product_uom' in \
            self.env['stock.move.line']._fields else 'quantity'
        # Cuenta TODA reserva viva. Una linea marcada como 'picked' sigue en el
        # quant hasta que se valida el albaran, pero ya esta comprometida: si se
        # excluye, la existencia liberada sale inflada.
        reserved = sum((ml[campo] or 0.0) for ml in reservas)
        return max(0.0, released_total - reserved)

    @staticmethod
    def _is_stock_tracked(product):
        if 'is_storable' in product._fields:
            return bool(product.is_storable)
        return product.type == 'product'

    def _bom_coverage(self, product, bom, qty, pool=None, totals=None):
        """Devuelve (cobertura 0..1, faltantes, necesidades) explotando la BoM.

        NOo: eruenta nadao: l pool: quien llama decide cuanto se va a fabricar de
        verdad y luego llama a `_bom_consume`. `needs` viene en None si la BoM no
        se pudo explotar, para poder distinguir un error tecnico de una  erasez.

        `pool`  e un diccionario compartido por todo el plan con la materia prima
        que va quedando; sin el, dos pruebas que comparten un mismo reactivo se
        declararian ambas cubiertas aunque juntas lo agoten.
        """
        if not bom or qty <= 0:
            return (1.0 if qty <= 0 else 0.0 if self.only_with_bom else 1.0), {}, {}
        if pool is None:
            pool = {}
        if totals is None:
            totals = {}
        try:
            _boms, bom_lines = bom.explode(product, qty / (bom.product_qty or 1.0))
        except Exception as exc:  # pragma: no cover - defensivo
            _logger.warning('No se pudo explotar la BoM de %s: %s', product.display_name, exc)
            return 0.0, {}, None

        # Se agrupa por componente: la misma MP puede aparecer en varias lineas
        # de la BoM (o en sub-BoMs) y hay que sumarla, no compararla suelta.
        needs = {}
        for bom_line, line_data in bom_lines:
            component = bom_line.product_id
            required = line_data.get('qty') or line_data.get('quantity') or 0.0
            if required <= 0 or component.type == 'service':
                continue
            if not self._is_stock_tracked(component):
                # Un componente que Odoo no inventaria (consumible puro) no puede
                # bloquear el plan: su existencia siempre seria cero.
                continue
            if component.id not in pool:
                libre = self._available_qty(component, componente=True)
                pool[component.id] = libre
                totals[component.id] = libre
            acc = needs.setdefault(
                component.id, {'component': component, 'required': 0.0})
            acc['required'] += required

        coverage = 1.0
        missing = {}
        for comp_id, data in needs.items():
            required = data['required']
            available = pool.get(comp_id, 0.0)
            ratio = min(1.0, available / required) if required > 0 else 1.0
            if float_compare(available, required, precision_digits=3) < 0:
                # Indexado por id: dos componentes distintos pueden compartir
                # nombre y uno taparia al otro.
                missing[comp_id] = {
                    'product_id': comp_id,
                    'name': data['component'].display_name,
                    'required': required,
                    'available': totals.get(comp_id, available),
                    'remaining': available,
                }
            coverage = min(coverage, ratio)
        return max(coverage, 0.0), missing, needs

    def _bom_consume(self, needs, pool, ratio):
        """Apartao: l pool la materia prima de lo que si se va a fabricar."""
        if not needs or ratio <= 0:
            return
        for comp_id, data in needs.items():
            pool[comp_id] = max(
                0.0, pool.get(comp_id, 0.0) - data['required'] * ratio)

    # ------------------------------------------------------------------
    # Ordenes de fabricacion
    # ------------------------------------------------------------------
    def action_create_mos(self):
        self.ensure_one()
        self._lock()
        if self.state != 'computed':
            raise UserError(_(
                'Solo se pueden generar ordenes desde un plan calculado. '
                'Estado actual: %s.', dict(
                    self._fields['state'].selection).get(self.state, self.state)))
        self.invalidate_recordset(['line_ids'])
        lines = self.line_ids.filtered(
            lambda l: l.supply_mode == 'manufacture' and l.qty_to_produce > 0
            and not l.production_id)
        if not lines:
            raise UserError(_('No hay lineas con cantidad a producir pendientes de orden.'))
        Production = self.env['mrp.production']
        created = Production.browse()
        for line in lines:
            if line.production_id:  # carrera: alguien la creo entre medias
                continue
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
    supply_mode = fields.Selection([
        ('manufacture', 'Fabricar'),
        ('buy', 'Comprar para reventa'),
        ('unknown', 'Sin origen definido'),
    ], string='Origen', default='manufacture')

    qty_history = fields.Float(string='Vendido en la ventana', digits='Product Unit of Measure')
    qty_daily = fields.Float(string='Demanda diaria', digits='Product Unit of Measure')
    qty_need = fields.Float(string='Necesidad del horizonte', digits='Product Unit of Measure')
    qty_on_hand = fields.Float(string='Disponible contado', digits='Product Unit of Measure')
    qty_free = fields.Float(string='Existencia libre total', digits='Product Unit of Measure')
    qty_released = fields.Float(string='Liberada por Calidad', digits='Product Unit of Measure')
    qty_pending_qc = fields.Float(string='Esperando liberacion', digits='Product Unit of Measure')
    qty_incoming = fields.Float(
        string='En camino', digits='Product Unit of Measure',
        help='Piezas ya compradas en ordenes de compra confirmadas y aun no recibidas.')
    qty_wip = fields.Float(string='En produccion', digits='Product Unit of Measure')
    qty_suggested = fields.Float(string='Sugerido', digits='Product Unit of Measure')
    mp_coverage = fields.Float(string='Cobertura MP (%)')
    qty_to_produce = fields.Float(string='A producir', digits='Product Unit of Measure')
    qty_to_buy = fields.Float(string='A comprar', digits='Product Unit of Measure')
    blocking_note = fields.Char(string='Materia prima que falta')
    production_id = fields.Many2one('mrp.production', string='Orden creada', readonly=True)

    status = fields.Selection([
        ('ok', 'Se puede producir'),
        ('partial', 'Alcanza parcial'),
        ('blocked', 'Bloqueado por materia prima'),
        ('buy', 'Hay que comprar'),
        ('nosource', 'Sin BoM ni proveedor'),
        ('none', 'Sin necesidad'),
    ], compute='_compute_status', store=True, string='Situacion')

    @api.depends('qty_suggested', 'qty_to_produce', 'qty_to_buy', 'supply_mode')
    def _compute_status(self):
        for line in self:
            if line.qty_suggested <= 0:
                line.status = 'none'
            elif line.supply_mode == 'buy':
                line.status = 'buy'
            elif line.supply_mode == 'unknown':
                line.status = 'nosource'
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
