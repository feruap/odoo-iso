# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AmunetPackagingPlan(models.Model):
    _name = 'amunet.packaging.plan'
    _description = 'Plan de empaque por orden de fabricacion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='Folio',
        default='Nuevo',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    production_id = fields.Many2one(
        'mrp.production',
        string='Orden de fabricacion',
        required=True,
        tracking=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        related='production_id.product_id',
        store=True,
        readonly=True,
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Producto maestro',
        related='product_id.product_tmpl_id',
        store=True,
        readonly=True,
    )
    product_qty = fields.Float(
        string='Piezas a empacar',
        related='production_id.product_qty',
        readonly=True,
    )
    lot_name = fields.Char(
        string='Lote',
        compute='_compute_lot_name',
        store=True,
        readonly=False,
        tracking=True,
    )
    expiration_text = fields.Char(
        string='Caducidad etiqueta',
        compute='_compute_lot_name',
        store=True,
        readonly=False,
    )

    trend_days = fields.Integer(string='Dias de tendencia', default=180, required=True)
    trend_date_from = fields.Date(string='Desde', compute='_compute_trend_dates', store=True)
    trend_date_to = fields.Date(string='Hasta', compute='_compute_trend_dates', store=True)
    trend_source_note = fields.Text(string='Fuente / criterio de tendencia')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('suggested', 'Sugerido'),
        ('approved', 'Aprobado'),
        ('done', 'Cerrado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft', required=True, tracking=True)

    line_ids = fields.One2many(
        'amunet.packaging.plan.line',
        'plan_id',
        string='Mezcla de empaque',
        copy=True,
    )
    total_approved_pieces = fields.Float(
        string='Piezas aprobadas',
        compute='_compute_totals',
    )
    total_approved_boxes = fields.Float(
        string='Cajas aprobadas',
        compute='_compute_totals',
    )
    total_suggested_pieces = fields.Float(
        string='Piezas sugeridas',
        compute='_compute_totals',
    )
    has_exact_mix = fields.Boolean(
        string='Mezcla exacta',
        compute='_compute_totals',
    )
    approved_by_id = fields.Many2one('res.users', string='Aprobado por', readonly=True)
    approved_date = fields.Datetime(string='Fecha aprobacion', readonly=True)
    closed_by_id = fields.Many2one('res.users', string='Cerrado por', readonly=True)
    closed_date = fields.Datetime(string='Fecha cierre', readonly=True)
    notes = fields.Html(string='Notas')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.packaging.plan'
                ) or 'PE/Nuevo'
        return super().create(vals_list)

    @api.depends('production_id.solution_lot_id', 'production_id.lot_producing_ids', 'production_id.amunet_expiration_text')
    def _compute_lot_name(self):
        for rec in self:
            lots = rec.production_id.lot_producing_ids.mapped('name')
            rec.lot_name = ', '.join(lots) or rec.production_id.solution_lot_id or ''
            rec.expiration_text = rec.production_id.amunet_expiration_text or ''

    @api.depends('trend_days')
    def _compute_trend_dates(self):
        today = fields.Date.context_today(self)
        for rec in self:
            days = rec.trend_days or 180
            rec.trend_date_to = today
            rec.trend_date_from = fields.Date.subtract(today, days=days)

    @api.depends('line_ids.suggested_box_qty', 'line_ids.suggested_piece_qty', 'line_ids.approved_box_qty', 'line_ids.approved_piece_qty', 'product_qty')
    def _compute_totals(self):
        for rec in self:
            rec.total_suggested_pieces = sum(rec.line_ids.mapped('suggested_piece_qty'))
            rec.total_approved_pieces = sum(rec.line_ids.mapped('approved_piece_qty'))
            rec.total_approved_boxes = sum(rec.line_ids.mapped('approved_box_qty'))
            rec.has_exact_mix = abs((rec.total_approved_pieces or 0.0) - (rec.product_qty or 0.0)) < 0.0001

    def _require_manager(self):
        if not (
            self.env.user.has_group('amunet_packaging_planning.group_packaging_manager')
            or self.env.user.has_group('amunet_production.group_production_supervisor')
            or self.env.user.has_group('amunet_quality.group_quality_supervisor')
            or self.env.user.has_group('amunet_quality.group_quality_manager')
        ):
            raise UserError(_('No tiene permisos para aprobar o cerrar planes de empaque.'))

    def _authorized_presentations(self):
        self.ensure_one()
        presentations = self.env['amunet.packaging.presentation'].search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('is_authorized', '=', True),
            ('active', '=', True),
        ], order='package_qty desc, id')
        if not presentations:
            raise UserError(_(
                'No hay presentaciones autorizadas para %s. Configure caja c/5, c/20 u otras presentaciones antes de planear.'
            ) % self.product_id.display_name)
        return presentations

    def _trend_by_presentation(self, presentations):
        self.ensure_one()
        trends = self.env['amunet.woo.sales.trend'].read_group(
            [
                ('presentation_id', 'in', presentations.ids),
                ('sale_date', '>=', self.trend_date_from),
                ('sale_date', '<=', self.trend_date_to),
            ],
            ['piece_qty:sum', 'box_qty:sum'],
            ['presentation_id'],
        )
        by_id = {
            row['presentation_id'][0]: {
                'piece_qty': row.get('piece_qty') or 0.0,
                'box_qty': row.get('box_qty') or 0.0,
            }
            for row in trends
            if row.get('presentation_id')
        }
        return by_id

    def _solve_mix(self, target_qty, presentations, trend_by_id):
        """Integer exact mix nearest to Woo piece-ratio targets."""
        target_qty = int(round(target_qty or 0))
        if target_qty <= 0:
            raise UserError(_('La orden no tiene cantidad a empacar.'))

        trend_total = sum((trend_by_id.get(p.id, {}).get('piece_qty') or 0.0) for p in presentations)
        if trend_total <= 0:
            targets = {p.id: target_qty / float(len(presentations)) for p in presentations}
        else:
            targets = {
                p.id: target_qty * (trend_by_id.get(p.id, {}).get('piece_qty') or 0.0) / trend_total
                for p in presentations
            }

        dp = {0: (0.0, {})}
        for presentation in presentations:
            size = presentation.package_qty
            next_dp = {}
            for used, (cost, counts) in dp.items():
                remaining = target_qty - used
                for boxes in range(0, (remaining // size) + 1):
                    pieces = boxes * size
                    new_used = used + pieces
                    new_cost = cost + abs(pieces - targets[presentation.id])
                    new_counts = dict(counts)
                    new_counts[presentation.id] = boxes
                    previous = next_dp.get(new_used)
                    if previous is None or new_cost < previous[0]:
                        next_dp[new_used] = (new_cost, new_counts)
            dp = next_dp

        if target_qty not in dp:
            sizes = ', '.join(str(p.package_qty) for p in presentations)
            raise UserError(_(
                'No existe combinacion exacta para %s piezas con presentaciones: %s. Ajuste cantidad o agregue una presentacion autorizada.'
            ) % (target_qty, sizes))
        return dp[target_qty][1], targets, trend_total

    def action_generate_suggestion(self):
        for rec in self:
            presentations = rec._authorized_presentations()
            trend_by_id = rec._trend_by_presentation(presentations)
            counts, targets, trend_total = rec._solve_mix(rec.product_qty, presentations, trend_by_id)
            rec.line_ids.unlink()
            line_commands = []
            for presentation in presentations:
                boxes = counts.get(presentation.id, 0)
                if boxes <= 0 and not trend_by_id.get(presentation.id, {}).get('piece_qty'):
                    continue
                trend_piece_qty = trend_by_id.get(presentation.id, {}).get('piece_qty') or 0.0
                ratio = trend_piece_qty / trend_total if trend_total else 0.0
                line_commands.append((0, 0, {
                    'presentation_id': presentation.id,
                    'trend_piece_qty': trend_piece_qty,
                    'trend_ratio': ratio,
                    'target_piece_qty': targets[presentation.id],
                    'suggested_box_qty': boxes,
                    'approved_box_qty': boxes,
                }))
            rec.write({
                'line_ids': line_commands,
                'state': 'suggested',
                'trend_source_note': _(
                    'Sugerencia calculada con ventas WooCommerce de los ultimos %s dias. Woo sugiere demanda; Odoo valida presentaciones autorizadas.'
                ) % rec.trend_days,
            })
            rec.message_post(body=_('Mezcla sugerida a partir de tendencia WooCommerce.'))

    def action_approve(self):
        for rec in self:
            rec._require_manager()
            if not rec.line_ids:
                raise UserError(_('Genere o capture una mezcla antes de aprobar.'))
            if not rec.has_exact_mix:
                raise UserError(_(
                    'La mezcla aprobada debe sumar exactamente %s piezas. Actualmente suma %s.'
                ) % (rec.product_qty, rec.total_approved_pieces))
            rec.write({
                'state': 'approved',
                'approved_by_id': self.env.user.id,
                'approved_date': fields.Datetime.now(),
            })
            rec.message_post(body=_('Plan de empaque aprobado.'))

    def action_close(self):
        for rec in self:
            rec._require_manager()
            if rec.state != 'approved':
                raise UserError(_('Solo puede cerrar un plan aprobado.'))
            rec.write({
                'state': 'done',
                'closed_by_id': self.env.user.id,
                'closed_date': fields.Datetime.now(),
            })
            rec.message_post(body=_('Plan de empaque cerrado.'))

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_open_label_wizard(self):
        self.ensure_one()
        first_line = self.line_ids.filtered(lambda line: line.approved_box_qty > 0)[:1]
        if not first_line:
            raise UserError(_('No hay cajas aprobadas para imprimir etiquetas.'))
        product = first_line.presentation_id.product_id or self.product_id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generar etiquetas'),
            'res_model': 'amunet.label.print.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': product.id,
                'default_lot_name': self.lot_name,
                'default_expiration_date_text': self.expiration_text,
                'default_quantity': int(first_line.approved_box_qty),
            },
        }


class AmunetPackagingPlanLine(models.Model):
    _name = 'amunet.packaging.plan.line'
    _description = 'Linea de plan de empaque'
    _order = 'package_qty desc, id'

    plan_id = fields.Many2one(
        'amunet.packaging.plan',
        string='Plan',
        required=True,
        ondelete='cascade',
    )
    presentation_id = fields.Many2one(
        'amunet.packaging.presentation',
        string='Presentacion',
        required=True,
    )
    package_qty = fields.Integer(
        related='presentation_id.package_qty',
        string='Pruebas por caja',
        store=True,
        readonly=True,
    )
    trend_piece_qty = fields.Float(string='Piezas vendidas Woo')
    trend_ratio = fields.Float(string='% tendencia')
    target_piece_qty = fields.Float(string='Objetivo por tendencia')

    suggested_box_qty = fields.Integer(string='Cajas sugeridas')
    suggested_piece_qty = fields.Integer(
        string='Piezas sugeridas',
        compute='_compute_pieces',
        store=True,
    )
    approved_box_qty = fields.Integer(string='Cajas aprobadas')
    approved_piece_qty = fields.Integer(
        string='Piezas aprobadas',
        compute='_compute_pieces',
        store=True,
    )
    label_qty = fields.Integer(
        string='Etiquetas a imprimir',
        compute='_compute_pieces',
        store=True,
    )
    manual_qty = fields.Integer(
        string='Manuales a surtir/imprimir',
        compute='_compute_pieces',
        store=True,
    )

    @api.depends('suggested_box_qty', 'approved_box_qty', 'package_qty', 'presentation_id.label_required', 'presentation_id.manual_required')
    def _compute_pieces(self):
        for line in self:
            line.suggested_piece_qty = (line.suggested_box_qty or 0) * (line.package_qty or 0)
            line.approved_piece_qty = (line.approved_box_qty or 0) * (line.package_qty or 0)
            line.label_qty = line.approved_box_qty if line.presentation_id.label_required else 0
            line.manual_qty = line.approved_box_qty if line.presentation_id.manual_required else 0

    @api.constrains('suggested_box_qty', 'approved_box_qty')
    def _check_box_qty(self):
        for line in self:
            if line.suggested_box_qty < 0 or line.approved_box_qty < 0:
                raise ValidationError(_('Las cajas no pueden ser negativas.'))
