# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Configuracion Actividades Produccion (Checklist de Fabricacion)
    amunet_req_history_log = fields.Boolean(string='Requiere Registro en Bitácora', default=True)
    amunet_req_calculations = fields.Boolean(string='Requiere Cálculos', default=True)
    amunet_weighing_range_text = fields.Char(string='Rango de Pesaje', default='± 0.0007', help='Ejemplo: ± 0.0007')
    amunet_req_dilution = fields.Boolean(string='Requiere Dilución de Reactivos', default=True)
    amunet_ph_adj_range_text = fields.Char(string='Tolerancia Ajuste pH', default='± 0.05', help='Ejemplo: ± 0.05')
    amunet_req_aforar = fields.Boolean(string='Requiere Aforar', default=True)
    amunet_req_quality_control = fields.Boolean(string='Requiere Análisis C.C', default=True, help='Si se desmarca, control de calidad no bloqueará la producción de este producto.')
    
    # Parametros Adicionales extraidos del Excel
    amunet_solution_dependency_id = fields.Many2one('product.product', string='Solución Requerida Previamente', help='Si requiere que otra solución se prepare primero (para lanzar la advertencia).')
    amunet_initial_ph = fields.Float(string='pH Inicial', help='El pH por defecto esperado para la solución (ej. 7.4)')
    amunet_expiration_text = fields.Char(string='Caducidad (Texto)', help='Tiempo de vida útil. Ejemplo: 6 Meses, 2.6 años')
