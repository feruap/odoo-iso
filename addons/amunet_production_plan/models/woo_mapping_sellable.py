# -*- coding: utf-8 -*-
"""Columna "Vendible" en la pantalla de mapeos Woo (accion 1109).

Muestra, junto a "Woo disponible", las piezas que el plan de produccion cuenta
como vendibles: lotes en anaquel con caducidad de al menos N meses (parametro
`amunet_production_plan.min_shelf_months`, 6 por omision). Asi Direccion,
Almacen y el plan ven el mismo numero.
"""
from odoo import api, fields, models


class AmunetWooProductMappingSellable(models.Model):
    _inherit = 'amunet.woo.product.mapping'

    odoo_sellable_qty = fields.Float(
        string='Vendible (>= N meses)', compute='_compute_odoo_sellable_qty',
        digits='Product Unit of Measure',
        help='Piezas en APT/Existencias cuyo lote caduca en al menos los meses '
             'minimos configurados (amunet_production_plan.min_shelf_months). '
             'Lo que caduca antes, o esta en caducidad corta / cortesia / retirar, '
             'cuenta como cero. Es el numero que usa el plan de produccion.')

    @api.depends('product_id')
    def _compute_odoo_sellable_qty(self):
        Plan = self.env['amunet.production.plan']
        months = Plan._default_min_shelf_months()
        locations = Plan._default_sellable_locations()
        for rec in self:
            if not rec.product_id:
                rec.odoo_sellable_qty = 0.0
                continue
            rec.odoo_sellable_qty = Plan._sellable_qty_for(
                rec.product_id, months=months, locations=locations,
                company=rec.company_id or self.env.company)
