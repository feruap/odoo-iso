from odoo import fields, models


class AmunetArea(models.Model):
    _name = 'amunet.area'
    _description = 'Área auditada'
    _order = 'secuencia, name'

    name = fields.Char(string='Área', required=True)
    secuencia = fields.Integer(default=10)
    active = fields.Boolean(default=True)
