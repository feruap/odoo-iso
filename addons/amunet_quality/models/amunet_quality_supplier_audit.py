# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AmunetQualitySupplierAudit(models.Model):
    _name = 'amunet.quality.supplier.audit'
    _description = 'Auditoría a Proveedor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'audit_date desc'

    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True, default='Nuevo')
    
    partner_id = fields.Many2one(
        'res.partner', 
        string='Proveedor', 
        required=True, 
        domain=[('supplier_rank', '>', 0)],
        tracking=True
    )
    
    audit_date = fields.Date(string='Fecha Auditoría', required=True, default=fields.Date.context_today, tracking=True)
    
    auditor_id = fields.Many2one('res.users', string='Auditor', default=lambda self: self.env.user, tracking=True)
    
    result = fields.Selection([
        ('pass', 'Aprobado'),
        ('conditional', 'Condicional'),
        ('fail', 'Rechazado')
    ], string='Resultado', required=True, tracking=True)
    
    report_file = fields.Binary(string='Informe de Auditoría')
    report_filename = fields.Char(string='Nombre Archivo')
    
    notes = fields.Text(string='Observaciones')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Realizada'),
        ('cancel', 'Cancelada')
    ], string='Estado', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('amunet.quality.supplier.audit') or 'AUD-PROV'
        return super(AmunetQualitySupplierAudit, self).create(vals_list)

    def action_confirm(self):
        self.ensure_one()
        # Actualizar estado del proveedor automáticamente
        if self.result == 'pass':
            self.partner_id.quality_status = 'approved'
            self.partner_id.last_audit_date = self.audit_date
        elif self.result == 'conditional':
            self.partner_id.quality_status = 'conditional'
            self.partner_id.last_audit_date = self.audit_date
        elif self.result == 'fail':
            self.partner_id.quality_status = 'rejected'
            self.partner_id.last_audit_date = self.audit_date
            
        self.state = 'done'
