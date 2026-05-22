# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Secuencia para el folio de la ORDEN DE PRODUCCION cuando se
    # fabrica este producto. Si esta vacio, la MO usa la secuencia
    # generica del picking_type (AMP/MO/NNNNN). Si esta lleno, el
    # folio sigue el patron Amunet (0526/01/VIH) y ese mismo nombre
    # se hereda al stock.lot del producto fabricado.
    mo_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia de folio MO',
        help='Si esta definida, las ordenes de produccion de este '
             'producto usaran esta secuencia (formato Amunet '
             '"MMAA/NN/ABR") y el lote del producto fabricado '
             'heredara el mismo nombre. Si esta vacia, se usa la '
             'secuencia generica del tipo de operacion.',
    )

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
