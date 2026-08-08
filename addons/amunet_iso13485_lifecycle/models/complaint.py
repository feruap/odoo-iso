from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AmunetQualityComplaint(models.Model):
    _name = 'amunet.quality.complaint'
    _description = 'Queja y retroalimentación ISO 13485'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'received_date desc, id desc'

    name = fields.Char(default='Nuevo', readonly=True, copy=False, tracking=True)
    state = fields.Selection([
        ('draft', 'Borrador'), ('received', 'Recibida'),
        ('investigation', 'En investigación'), ('response', 'Respuesta pendiente'),
        ('closed', 'Cerrada'), ('rejected', 'No procedente'),
    ], default='draft', required=True, tracking=True)
    source = fields.Selection([
        ('customer', 'Cliente'), ('distributor', 'Distribuidor'),
        ('healthcare', 'Profesional de salud'), ('internal', 'Interna'),
        ('authority', 'Autoridad'), ('other', 'Otro'),
    ], default='customer', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Reportante / cliente', tracking=True)
    contact_name = fields.Char(string='Contacto')
    contact_email = fields.Char(string='Correo')
    contact_phone = fields.Char(string='Teléfono')
    received_date = fields.Datetime(default=fields.Datetime.now, required=True, tracking=True)
    acknowledgement_date = fields.Datetime(string='Fecha de acuse', readonly=True)
    response_due_date = fields.Date(string='Fecha compromiso de respuesta')
    response_date = fields.Datetime(string='Fecha de respuesta', readonly=True)
    category = fields.Selection([
        ('quality', 'Calidad / desempeño'), ('labeling', 'Etiquetado / IFU'),
        ('delivery', 'Entrega'), ('service', 'Servicio'), ('safety', 'Seguridad'),
        ('other', 'Otro'),
    ], default='quality', required=True, tracking=True)
    severity = fields.Selection([
        ('low', 'Baja'), ('medium', 'Media'), ('high', 'Alta'), ('critical', 'Crítica'),
    ], default='medium', required=True, tracking=True)
    description = fields.Html(string='Descripción de la queja', required=True)
    investigation = fields.Html(string='Investigación')
    root_cause = fields.Html(string='Causa raíz')
    disposition = fields.Html(string='Disposición / acciones')
    response_text = fields.Html(string='Respuesta al reportante')
    effectiveness_evidence = fields.Html(string='Evidencia de efectividad')
    product_id = fields.Many2one('product.product', string='Producto afectado', tracking=True)
    lot_id = fields.Many2one('stock.lot', string='Lote afectado', domain="[('product_id', '=', product_id)]", tracking=True)
    capa_id = fields.Many2one('amunet.quality.capa', string='CAPA', readonly=True, copy=False)
    change_control_id = fields.Many2one('amunet.change.control', string='Control de cambio', readonly=True, copy=False)
    tecnovigilance_id = fields.Many2one('amunet.quality.tecno.incident', string='Tecnovigilancia', readonly=True, copy=False)
    risk_item_ids = fields.One2many('amunet.risk.item', 'complaint_id', string='Riesgos relacionados')
    owner_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Responsable', tracking=True)
    acknowledged_by_id = fields.Many2one('res.users', readonly=True, string='Acuse por')
    closed_by_id = fields.Many2one('res.users', readonly=True, string='Cerrada por')
    closed_date = fields.Datetime(readonly=True)
    month = fields.Date(compute='_compute_month', store=True, index=True)

    @api.depends('received_date')
    def _compute_month(self):
        for rec in self:
            rec.month = fields.Date.to_date(rec.received_date).replace(day=1) if rec.received_date else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('amunet.quality.complaint') or 'QUE-NUEVO'
        return super().create(vals_list)

    def _require_quality(self):
        if not (self.env.user.has_group('amunet_quality.group_quality_supervisor') or self.env.user.has_group('amunet_quality.group_quality_manager')):
            raise UserError(_('Solo Calidad puede ejecutar esta transición.'))

    def action_receive(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Solo puede recibirse una queja en borrador.'))
            rec._require_quality()
            rec.write({'state': 'received', 'acknowledgement_date': fields.Datetime.now(), 'acknowledged_by_id': self.env.user.id})

    def action_investigate(self):
        for rec in self:
            if rec.state != 'received':
                raise UserError(_('La investigación inicia después del acuse.'))
            rec._require_quality()
            rec.write({'state': 'investigation'})

    def action_prepare_response(self):
        for rec in self:
            if rec.state != 'investigation' or not rec.investigation:
                raise UserError(_('Documente la investigación antes de preparar la respuesta.'))
            rec._require_quality()
            rec.write({'state': 'response'})

    def action_close(self):
        for rec in self:
            if rec.state != 'response' or not rec.response_text or not rec.effectiveness_evidence:
                raise UserError(_('Capture la respuesta y evidencia de efectividad antes de cerrar.'))
            rec._require_quality()
            rec.write({'state': 'closed', 'response_date': fields.Datetime.now(), 'closed_by_id': self.env.user.id, 'closed_date': fields.Datetime.now()})

    def action_create_capa(self):
        self.ensure_one()
        if self.capa_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'amunet.quality.capa',
                'res_id': self.capa_id.id,
                'view_mode': 'form',
            }
        capa = self.env['amunet.quality.capa'].create({
            'title': _('CAPA por queja %s') % self.name, 'product_id': self.product_id.id,
            'investigation_notes': self.description,
            'severity': 'critical' if self.severity in ('high', 'critical') else self.severity,
        })
        self.capa_id = capa
        return {'type': 'ir.actions.act_window', 'res_model': 'amunet.quality.capa', 'res_id': capa.id, 'view_mode': 'form'}

    @api.constrains('lot_id', 'product_id')
    def _check_lot_product(self):
        for rec in self:
            if rec.lot_id and rec.product_id and rec.lot_id.product_id != rec.product_id:
                raise ValidationError(_('El lote debe corresponder al producto afectado.'))
