# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_quality_control = fields.Boolean(
        string='Es Control de Calidad',
        compute='_compute_is_quality_control',
        store=True,
        help='Indica si este picking es de control de calidad'
    )
    is_storage = fields.Boolean(
        string='Es almacenamiento',
        compute='_compute_is_storage',
        store=True,
        help='Indica si este picking es de almacenamiento'
    )
    is_reception = fields.Boolean(
        string='Es recepcion',
        compute='_compute_is_reception',
        store=True,
        help='Indica si este picking es de recepcion'
    )

    # Flujo de aprobación para traslados internos
    transfer_approved = fields.Boolean(string='Aprobado', default=False, copy=False, tracking=True)
    transfer_approved_by = fields.Many2one('res.users', string='Aprobado por', readonly=True, copy=False)
    transfer_approved_date = fields.Datetime(string='Fecha aprobación', readonly=True, copy=False)

    transfer_done_by_operator = fields.Boolean(string='Realizado por almacenista', default=False, copy=False, tracking=True)
    transfer_done_by = fields.Many2one('res.users', string='Realizado por', readonly=True, copy=False)
    transfer_done_date = fields.Datetime(string='Fecha realización', readonly=True, copy=False)

    transfer_verified = fields.Boolean(string='Verificado', default=False, copy=False, tracking=True)
    transfer_verified_by = fields.Many2one('res.users', string='Verificado por', readonly=True, copy=False)
    transfer_verified_date = fields.Datetime(string='Fecha verificación', readonly=True, copy=False)

    date_display = fields.Char(
        string='Fecha (DD.MM.AA)',
        compute='_compute_date_display',
        inverse='_inverse_date_display',
    )
    transfer_flow_state = fields.Selection([
        ('draft', 'Borrador'),
        ('waiting', 'En espera de aprobación'),
        ('approved', 'Aprobado — por realizar'),
        ('executed', 'Realizado — por verificar'),
        ('verified', 'Verificado'),
        ('cancel', 'Cancelado'),
    ], string='Estado del traslado', compute='_compute_transfer_flow_state')

    @api.depends('state', 'picking_type_id', 'transfer_approved', 'transfer_done_by_operator')
    def _compute_transfer_flow_state(self):
        for rec in self:
            if rec.picking_type_code != 'internal':
                rec.transfer_flow_state = False
            elif rec.state == 'cancel':
                rec.transfer_flow_state = 'cancel'
            elif rec.state == 'done':
                rec.transfer_flow_state = 'verified'
            elif rec.transfer_done_by_operator:
                rec.transfer_flow_state = 'executed'
            elif rec.transfer_approved:
                rec.transfer_flow_state = 'approved'
            elif rec.state == 'draft':
                rec.transfer_flow_state = 'draft'
            else:
                rec.transfer_flow_state = 'waiting'

    @api.depends('scheduled_date')
    def _compute_date_display(self):
        for rec in self:
            rec.date_display = rec.scheduled_date.strftime('%d.%m.%y') if rec.scheduled_date else ''

    def _inverse_date_display(self):
        for rec in self:
            if not rec.date_display:
                continue
            try:
                dt = datetime.strptime(rec.date_display.strip(), '%d.%m.%y')
                if rec.scheduled_date:
                    dt = dt.replace(hour=rec.scheduled_date.hour, minute=rec.scheduled_date.minute)
                rec.scheduled_date = dt
            except ValueError:
                pass

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'partner_id' in fields_list:
            picking_type_id = (
                defaults.get('picking_type_id')
                or self.env.context.get('default_picking_type_id')
            )
            if picking_type_id:
                pt = self.env['stock.picking.type'].browse(picking_type_id)
                if pt.code == 'internal':
                    defaults['partner_id'] = self.env.user.partner_id.id
        return defaults

    @api.constrains('location_id', 'location_dest_id', 'picking_type_code')
    def _check_locations_different(self):
        for rec in self:
            if (rec.picking_type_code == 'internal'
                    and rec.location_id
                    and rec.location_dest_id
                    and rec.location_id == rec.location_dest_id):
                raise ValidationError(_(
                    'La ubicación de origen no puede ser la misma que la de destino.'
                ))

    @api.depends('picking_type_id', 'picking_type_id.is_quality_control')
    def _compute_is_quality_control(self):
        for record in self:
            record.is_quality_control = (
                record.picking_type_id.is_quality_control if record.picking_type_id else False
            )

    @api.depends('picking_type_id', 'picking_type_id.is_storage')
    def _compute_is_storage(self):
        for record in self:
            record.is_storage = (
                record.picking_type_id.is_storage if record.picking_type_id else False
            )

    @api.depends('picking_type_id', 'picking_type_id.is_reception')
    def _compute_is_reception(self):
        for record in self:
            record.is_reception = (
                record.picking_type_id.is_reception if record.picking_type_id else False
            )

    def action_confirm(self):
        # Para traslados internos: crear moves padre para move_lines huérfanas (del borrador)
        for picking in self:
            if picking.picking_type_code != 'internal':
                continue
            orphan_lines = picking.move_line_ids.filtered(lambda l: not l.move_id and l.product_id)
            for line in orphan_lines:
                move = self.env['stock.move'].create({
                    'name': line.product_id.display_name,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id or line.product_id.uom_id.id,
                    'product_uom_qty': line.qty_demanded or line.quantity or 1.0,
                    'picking_id': picking.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'state': 'draft',
                })
                line.move_id = move

        res = super().action_confirm()

        for picking in self:
            if picking.picking_type_code == 'incoming' and picking.state == 'confirmed':
                # Evitar doble action_assign cuando reservation_method='at_confirm'
                # ya creó líneas de movimiento. Consultamos BD directamente para
                # evitar falsos negativos por caché del ORM.
                self.env.cr.execute(
                    "SELECT id FROM stock_move_line WHERE picking_id=%s LIMIT 1",
                    (picking.id,)
                )
                if self.env.cr.fetchone():
                    picking.invalidate_recordset(['move_line_ids', 'state'])
                    picking.move_ids.write({'state': 'assigned'})
                    continue
                try:
                    picking.action_assign()
                    if picking.state not in ('assigned', 'done', 'cancel'):
                        picking.move_ids.write({'state': 'assigned'})
                except Exception:
                    picking.move_ids.write({'state': 'assigned'})
            elif picking.picking_type_code == 'internal' and picking.state == 'confirmed':
                try:
                    picking.action_assign()
                except Exception:
                    pass
        return res

    def action_transfer_approve(self):
        for rec in self:
            if rec.picking_type_code != 'internal':
                raise UserError(_('Solo se pueden aprobar traslados internos.'))
            rec.transfer_approved = True
            rec.transfer_approved_by = self.env.user
            rec.transfer_approved_date = fields.Datetime.now()

    def action_transfer_mark_done(self):
        for rec in self:
            if rec.picking_type_code != 'internal':
                raise UserError(_('Acción solo válida para traslados internos.'))
            # Precargar quantity = qty_demanded como punto de partida para la verificación
            for line in rec.move_line_ids:
                if not line.quantity and line.qty_demanded:
                    line.quantity = line.qty_demanded
            rec.transfer_done_by_operator = True
            rec.transfer_done_by = self.env.user
            rec.transfer_done_date = fields.Datetime.now()

    def action_transfer_verify(self):
        self.ensure_one()
        if self.picking_type_code != 'internal':
            raise UserError(_('Acción solo válida para traslados internos.'))
        self.transfer_verified = True
        self.transfer_verified_by = self.env.user
        self.transfer_verified_date = fields.Datetime.now()
        return self.button_validate()

    def _action_done(self):
        res = super()._action_done()
        for picking in self:
            for line in picking.move_line_ids:
                if line.lot_id:
                    vals_sync = {}
                    if line.factory_lot_id and line.lot_id.factory_lot_id != line.factory_lot_id:
                        vals_sync['factory_lot_id'] = line.factory_lot_id.id
                    if line.manufacturing_date and line.lot_id.manufacturing_date != line.manufacturing_date:
                        vals_sync['manufacturing_date'] = line.manufacturing_date
                    if line.expiration_date and line.lot_id.expiration_date != line.expiration_date:
                        vals_sync['expiration_date'] = line.expiration_date
                    if line.removal_date and line.lot_id.removal_date != line.removal_date:
                        vals_sync['removal_date'] = line.removal_date
                    if vals_sync:
                        line.lot_id.sudo().write(vals_sync)
        return res
