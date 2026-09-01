from odoo import fields, models


class AmunetRiskMatrix(models.Model):
    _name = 'amunet.risk.matrix'
    _description = 'Criterios de Clasificación NPR'
    _order = 'npr_min'

    name = fields.Char(string='Clasificación', required=True)
    nivel = fields.Selection([
        ('alto', 'Alto riesgo de falla'),
        ('medio', 'Probabilidad media de riesgo'),
        ('bajo', 'Bajo riesgo de falla'),
        ('ninguno', 'Sin riesgo'),
    ], string='Nivel', required=True)
    npr_min = fields.Integer(string='NPR mínimo')
    npr_max = fields.Integer(string='NPR máximo')
    descripcion = fields.Char(string='Descripción')
    accion_requerida = fields.Char(string='Acción requerida')
    color = fields.Integer(string='Color')
