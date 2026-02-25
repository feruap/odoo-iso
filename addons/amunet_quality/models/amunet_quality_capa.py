# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AmunetQualityCAPA(models.Model):
    """
    Acciones Correctivas y Preventivas (CAPA).
    ISO 13485:8.5.2 (Correctiva) y 8.5.3 (Preventiva).
    
    Gestiona la investigación, causa raíz y resolución de no conformidades.
    """
    _name = 'amunet.quality.capa'
    _description = 'Acción Correctiva/Preventiva'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Referencia',
        required=True,
        copy=False,
        readonly=True,
        default='Nuevo'
    )

    title = fields.Char(string='Título del Problema', required=True)

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('investigation', 'Investigación / Causa Raíz'),
        ('action_plan', 'Plan de Acción'),
        ('verification', 'Verificación de Efectividad'),
        ('closed', 'Cerrado'),
        ('cancel', 'Cancelado')
    ], string='Estado', default='draft', required=True, tracking=True)

    # ========== Origen del Problema ==========

    source_check_id = fields.Many2one(
        'amunet.quality.check',
        string='Control de Calidad Origen',
        readonly=True
    )

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        required=True
    )

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lote',
        domain="[('product_id', '=', product_id)]"
    )

    severity = fields.Selection([
        ('low', 'Baja (Menor)'),
        ('medium', 'Media (Mayor)'),
        ('critical', 'Crítica (Seguridad)'),
    ], string='Severidad', default='medium', required=True, tracking=True)

    # ========== Investigación (D4) ==========

    investigation_notes = fields.Html(
        string='Notas de Investigación',
        help='Descripción detallada de la investigación realizada'
    )

    root_cause = fields.Html(
        string='Causa Raíz',
        help='Análisis de la causa raíz (5 Porqués, Ishikawa, etc.)'
    )

    # ========== Plan de Acción (D5-D6) ==========

    containment_actions = fields.Html(
        string='Acciones de Contención',
        help='Acciones inmediatas para contener el problema'
    )

    corrective_actions = fields.Html(
        string='Acciones Correctivas',
        help='Acciones a largo plazo para eliminar la causa raíz'
    )

    target_date = fields.Date(string='Fecha Objetivo')

    # ========== Verificación (D7-D8) ==========

    verification_notes = fields.Html(
        string='Verificación de Efectividad',
        help='Evidencia de que las acciones eliminaron el problema'
    )
    
    user_responsible_id = fields.Many2one(
        'res.users',
        string='Responsable',
        default=lambda self: self.env.user,
        tracking=True
    )

    # ========== Métodos ==========

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('amunet.quality.capa') or 'CAPA-000'
        return super().create(vals_list)

    def action_investigation(self):
        self.write({'state': 'investigation'})

    def action_plan(self):
        self.write({'state': 'action_plan'})

    def action_verification(self):
        self.write({'state': 'verification'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        self.write({'state': 'cancel'})
