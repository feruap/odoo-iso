# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

CLASIFICACIONES = [
    ('MP', 'MP - Materia Prima'),
    ('MI', 'MI - Material Impreso'),
    ('SP', 'SP - Producto Semiprocesado (granel)'),
    ('ST', 'ST - Producto Semiterminado'),
    ('PT', 'PT - Producto Terminado'),
]


class AmunetClaveAbreviatura(models.Model):
    _name = 'amunet.clave.abreviatura'
    _description = 'Catálogo de abreviaturas para claves de productos'
    _order = 'clasificacion, abreviatura'

    clasificacion = fields.Selection(
        CLASIFICACIONES, string='Clasificación', required=True)
    name = fields.Char(string='Sub-categoría / Tipo', required=True)
    abreviatura = fields.Char(string='Abreviatura', required=True, size=4,
                              help="3 letras (norma nueva). Algunas históricas tienen 2-4.")
    prefijo = fields.Char(string='Prefijo de clave', compute='_compute_prefijo',
                          store=True, help="Clasificación + abreviatura. Ej: MPCAR")
    ejemplos = fields.Char(string='Ejemplos / descripción')
    active = fields.Boolean(default=True)

    @api.depends('clasificacion', 'abreviatura')
    def _compute_prefijo(self):
        for r in self:
            r.prefijo = '%s%s' % (r.clasificacion or '', (r.abreviatura or '').upper())

    @api.constrains('clasificacion', 'abreviatura')
    def _check_prefijo_unico(self):
        for r in self:
            dup = self.search([
                ('clasificacion', '=', r.clasificacion),
                ('abreviatura', '=', r.abreviatura),
                ('id', '!=', r.id),
            ], limit=1)
            if dup:
                raise ValidationError(_(
                    "Ya existe la abreviatura '%s' en la clasificación %s."
                ) % (r.abreviatura, r.clasificacion))
