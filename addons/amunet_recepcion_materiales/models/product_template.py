# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    amunet_requires_quarantine = fields.Boolean(
        'Requiere inspección de Calidad',
        help='Si está activo, al recibir este material irá a AMP/Control de calidad '
             'antes de pasar a existencias. Si se deja sin marcar, hereda el valor '
             'de la categoría del producto.',
    )

    amunet_destino_almacen = fields.Selection(
        [('mp', 'Materia prima (AMP)'),
         ('adt', 'Distribución (ADT)'),
         ('ambos', 'Ambos — se elige al pedirlo')],
        string='Almacén donde vive',
        default='mp',
        required=True,
        help='Dónde entra este producto cuando se compra.\n'
             '- Materia prima: se consume en fabricación.\n'
             '- Distribución: se compra para vender.\n'
             '- Ambos: depende de para qué se pida; la solicitud de compra '
             'pregunta a cuál llega.',
    )

    # Se conserva como campo calculado porque la liberación de Calidad ya lo
    # usa para mandar el material a ADT. Solo es verdadero cuando el producto
    # vive EXCLUSIVAMENTE en distribución: si es 'ambos', el destino lo decide
    # la compra y no se debe re-enrutar solo.
    amunet_va_a_distribucion = fields.Boolean(
        'Va a distribución ADT',
        compute='_compute_amunet_va_a_distribucion',
        store=True,
        readonly=True,
    )

    @api.depends('amunet_destino_almacen')
    def _compute_amunet_va_a_distribucion(self):
        for tmpl in self:
            tmpl.amunet_va_a_distribucion = tmpl.amunet_destino_almacen == 'adt'

    @api.onchange('categ_id')
    def _onchange_categ_quarantine(self):
        if self.categ_id and not self.amunet_requires_quarantine:
            self.amunet_requires_quarantine = self.categ_id.amunet_requires_quarantine

    def _amunet_effective_requires_quarantine(self):
        """Devuelve True si el producto o su categoría requieren inspección."""
        self.ensure_one()
        return self.amunet_requires_quarantine or self.categ_id.amunet_requires_quarantine
