# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    quality_status = fields.Selection([
            ('draft', 'Sin Clasificar'),
            ('approved', 'Aprobado'),
            ('conditional', 'Aprobado Condicionalmente'),
            ('rejected', 'Rechazado')
        ], string='Estado de Calidad', default='draft',
        help="Estado de calificación del proveedor según auditorías de calidad.",
        tracking=True
    )

    last_audit_date = fields.Date(string='Última Auditoría', readonly=True)
    next_audit_date = fields.Date(string='Próxima Auditoría')
    
    quality_notes = fields.Text(string='Notas de Calidad', help="Observaciones del departamento de calidad.")

    audit_ids = fields.One2many(
        'amunet.quality.supplier.audit',
        'partner_id',
        string='Auditorías de Calidad'
    )

    @api.depends('audit_ids.result')
    def _compute_audit_status(self):
        # Lógica futura para auto-calcular estado si se requiere
        pass
