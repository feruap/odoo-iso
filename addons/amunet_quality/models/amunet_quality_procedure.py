# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AmunetQualityProcedure(models.Model):
    """
    Procedimientos Operativos Estándar (SOPs) e Instrucciones de Trabajo.
    ISO 13485:4.2.3 - Control de documentos.
    
    Gestiona los documentos que deben estar disponibles en el punto de uso.
    """
    _name = 'amunet.quality.procedure'
    _description = 'Procedimiento de Calidad (SOP)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code, version desc'

    name = fields.Char(
        string='Título del Procedimiento',
        required=True,
        tracking=True
    )

    code = fields.Char(
        string='Código de Documento',
        required=True,
        index=True,
        tracking=True,
        help='Ej: SOP-CAL-001'
    )

    version = fields.Integer(
        string='Versión',
        default=1,
        required=True,
        tracking=True
    )

    active = fields.Boolean(
        default=True,
        tracking=True,
        help='Indica si esta es la versión vigente del documento'
    )

    document_file = fields.Binary(
        string='Archivo del Documento',
        required=True,
        attachment=True,
        help='Archivo PDF/Docx con el procedimiento'
    )

    document_filename = fields.Char(string='Nombre de archivo')

    product_ids = fields.Many2many(
        'product.product',
        string='Productos Relacionados',
        help='Productos a los que aplica este procedimiento'
    )

    description = fields.Text(string='Descripción / Resumen')

    # ========== Control de Versiones Simple ==========

    @api.model_create_multi
    def create(self, vals_list):
        """
        Al crear una nueva versión con el mismo código,
        archivar automáticamente las versiones anteriores.
        """
        for vals in vals_list:
            if vals.get('active', True) and vals.get('code'):
                # Archivar otros con el mismo código
                old_versions = self.search([
                    ('code', '=', vals['code']),
                    ('active', '=', True)
                ])
                if old_versions:
                    old_versions.write({'active': False})
        
        return super().create(vals_list)

    def write(self, vals):
        """
        Si se activa un documento, desactivar otros con el mismo código.
        """
        if vals.get('active'):
            for record in self:
                if record.code:
                    old_versions = self.search([
                        ('code', '=', record.code),
                        ('id', '!=', record.id),
                        ('active', '=', True)
                    ])
                    if old_versions:
                        old_versions.write({'active': False})
        
        return super().write(vals)
