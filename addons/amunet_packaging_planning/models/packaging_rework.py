# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AmunetPackagingRework(models.Model):
    _name = 'amunet.packaging.rework'
    _description = 'Reacondicionamiento de empaque autorizado'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='Folio',
        default='Nuevo',
        readonly=True,
        required=True,
        copy=False,
        tracking=True,
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Producto maestro',
        required=True,
        tracking=True,
    )
    source_presentation_id = fields.Many2one(
        'amunet.packaging.presentation',
        string='Presentacion origen',
        required=True,
        domain="[('product_tmpl_id', '=', product_tmpl_id), ('is_authorized', '=', True)]",
        tracking=True,
    )
    target_presentation_id = fields.Many2one(
        'amunet.packaging.presentation',
        string='Presentacion destino',
        required=True,
        domain="[('product_tmpl_id', '=', product_tmpl_id), ('is_authorized', '=', True)]",
        tracking=True,
    )
    lot_id = fields.Many2one('stock.lot', string='Lote')
    lot_name = fields.Char(string='Lote texto', tracking=True)
    expiration_text = fields.Char(string='Caducidad etiqueta')
    location_id = fields.Many2one('stock.location', string='Ubicacion', domain="[('usage', '=', 'internal')]")

    source_box_qty = fields.Integer(string='Cajas origen', required=True, default=1, tracking=True)
    source_piece_qty = fields.Integer(string='Piezas origen', compute='_compute_quantities', store=True)
    target_box_qty = fields.Integer(string='Cajas destino', compute='_compute_quantities', store=True, readonly=False)
    target_piece_qty = fields.Integer(string='Piezas destino', compute='_compute_quantities', store=True)

    reason = fields.Text(string='Motivo', required=True)
    label_required = fields.Boolean(string='Requiere etiquetas nuevas', default=True)
    manual_required = fields.Boolean(string='Requiere manuales', default=True)
    label_printed = fields.Boolean(string='Etiquetas impresas', tracking=True)
    manual_ready = fields.Boolean(string='Manuales listos', tracking=True)
    quality_notes = fields.Html(string='Verificacion Calidad')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('qc_review', 'En revision Calidad'),
        ('approved', 'Aprobado'),
        ('done', 'Cerrado'),
        ('cancel', 'Cancelado'),
    ], default='draft', required=True, tracking=True)

    requested_by_id = fields.Many2one(
        'res.users',
        string='Solicitado por',
        default=lambda self: self.env.user,
        readonly=True,
    )
    quality_approved_by_id = fields.Many2one('res.users', string='Aprobo Calidad', readonly=True)
    quality_approved_date = fields.Datetime(string='Fecha aprobacion Calidad', readonly=True)
    done_by_id = fields.Many2one('res.users', string='Cerrado por', readonly=True)
    done_date = fields.Datetime(string='Fecha cierre', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'amunet.packaging.rework'
                ) or 'RA/Nuevo'
        return super().create(vals_list)

    @api.onchange('source_presentation_id')
    def _onchange_source_presentation(self):
        for rec in self:
            if rec.source_presentation_id:
                rec.product_tmpl_id = rec.source_presentation_id.product_tmpl_id

    @api.depends('source_box_qty', 'source_presentation_id.package_qty', 'target_presentation_id.package_qty')
    def _compute_quantities(self):
        for rec in self:
            rec.source_piece_qty = (rec.source_box_qty or 0) * (rec.source_presentation_id.package_qty or 0)
            target_size = rec.target_presentation_id.package_qty or 0
            if target_size and rec.source_piece_qty:
                rec.target_box_qty = rec.source_piece_qty // target_size if rec.source_piece_qty % target_size == 0 else 0
                rec.target_piece_qty = rec.target_box_qty * target_size
            else:
                rec.target_box_qty = 0
                rec.target_piece_qty = 0

    @api.constrains('source_presentation_id', 'target_presentation_id', 'source_box_qty', 'target_box_qty')
    def _check_rework(self):
        for rec in self:
            if rec.source_box_qty <= 0:
                raise ValidationError(_('Las cajas origen deben ser mayores a cero.'))
            if rec.source_presentation_id and rec.target_presentation_id:
                if rec.source_presentation_id == rec.target_presentation_id:
                    raise ValidationError(_('Origen y destino deben ser presentaciones distintas.'))
                if rec.source_presentation_id.product_tmpl_id != rec.target_presentation_id.product_tmpl_id:
                    raise ValidationError(_('Origen y destino deben ser del mismo producto.'))
                if not rec.source_presentation_id.is_authorized or not rec.target_presentation_id.is_authorized:
                    raise ValidationError(_('Solo se puede reacondicionar entre presentaciones autorizadas.'))
                if rec.target_piece_qty != rec.source_piece_qty:
                    raise ValidationError(_('La conversion debe conservar exactamente el numero de piezas.'))

    def _require_quality(self):
        if not (
            self.env.user.has_group('amunet_quality.group_quality_supervisor')
            or self.env.user.has_group('amunet_quality.group_quality_manager')
        ):
            raise UserError(_('Solo Calidad autorizada puede aprobar reacondicionamientos.'))

    def _require_packaging(self):
        if not (
            self.env.user.has_group('amunet_packaging_planning.group_packaging_manager')
            or self.env.user.has_group('amunet_production.group_production_supervisor')
            or self.env.user.has_group('amunet_material_request.group_material_warehouse')
        ):
            raise UserError(_('Solo Empaque/Produccion autorizada puede ejecutar reacondicionamientos.'))

    def action_submit_qc(self):
        for rec in self:
            rec._require_packaging()
            if not rec.reason:
                raise UserError(_('Capture el motivo del reacondicionamiento.'))
            if rec.target_piece_qty != rec.source_piece_qty:
                raise UserError(_('La conversion no conserva las piezas.'))
            rec.write({'state': 'qc_review'})
            rec.message_post(body=_('Reacondicionamiento enviado a revision de Calidad.'))

    def action_quality_approve(self):
        for rec in self:
            rec._require_quality()
            if rec.state != 'qc_review':
                raise UserError(_('Solo se aprueba desde En revision Calidad.'))
            rec.write({
                'state': 'approved',
                'quality_approved_by_id': self.env.user.id,
                'quality_approved_date': fields.Datetime.now(),
            })
            rec.message_post(body=_('Calidad aprobo el reacondicionamiento.'))

    def action_mark_print_ready(self):
        for rec in self:
            rec._require_packaging()
            vals = {}
            if rec.label_required:
                vals['label_printed'] = True
            if rec.manual_required:
                vals['manual_ready'] = True
            rec.write(vals)
            rec.message_post(body=_('Etiquetas/manuales marcados como listos.'))

    def action_done(self):
        for rec in self:
            rec._require_packaging()
            if rec.state != 'approved':
                raise UserError(_('Calidad debe aprobar antes de cerrar.'))
            if rec.label_required and not rec.label_printed:
                raise UserError(_('Falta marcar etiquetas impresas.'))
            if rec.manual_required and not rec.manual_ready:
                raise UserError(_('Falta marcar manuales listos.'))
            rec.write({
                'state': 'done',
                'done_by_id': self.env.user.id,
                'done_date': fields.Datetime.now(),
            })
            rec.message_post(body=_('Reacondicionamiento cerrado.'))

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_open_label_wizard(self):
        self.ensure_one()
        product = self.target_presentation_id.product_id
        if not product:
            product = self.env['product.product'].search([
                ('product_tmpl_id', '=', self.product_tmpl_id.id)
            ], limit=1)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generar etiquetas'),
            'res_model': 'amunet.label.print.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': product.id,
                'default_lot_name': self.lot_name or (self.lot_id.name if self.lot_id else ''),
                'default_expiration_date_text': self.expiration_text,
                'default_quantity': int(self.target_box_qty or 1),
            },
        }
