# -*- coding: utf-8 -*-
"""
Redefine fields de precio con groups= a nivel field (no solo en vistas).

NOTA: list_price y standard_price en product.template/product.product NO se
bloquean aquí a nivel ORM porque ese campo aparece en demasiadas vistas de
otros módulos (inventario, manufactura, calidad) y causa AccessError en cascada.
El ocultamiento de esos campos se maneja exclusivamente via groups= en las
vistas XML (product_views.xml). El bloqueo ORM aplica solo a campos de compra,
donde el riesgo de exposición accidental es real y acotado.

Si un reporte necesita incluir costos (standard_price o list_price), se
requiere autorización expresa de Dirección antes de agregarlo.
"""
from odoo import api, models, fields

PRICE_GROUP = 'amunet_price_visibility.group_price_viewer'


class ProductTemplatePV(models.Model):
    _inherit = 'product.template'

    amunet_price_visible = fields.Boolean(compute='_compute_amunet_price_visible')

    @api.depends_context('uid')
    def _compute_amunet_price_visible(self):
        can_see = self.env.user.has_group(PRICE_GROUP)
        for rec in self:
            rec.amunet_price_visible = can_see


class ProductProductPV(models.Model):
    _inherit = 'product.product'

    amunet_price_visible = fields.Boolean(compute='_compute_amunet_price_visible')

    @api.depends_context('uid')
    def _compute_amunet_price_visible(self):
        can_see = self.env.user.has_group(PRICE_GROUP)
        for rec in self:
            rec.amunet_price_visible = can_see


class ProductSupplierinfoPV(models.Model):
    _inherit = 'product.supplierinfo'

    amunet_price_visible = fields.Boolean(compute='_compute_amunet_price_visible')

    @api.depends_context('uid')
    def _compute_amunet_price_visible(self):
        can_see = self.env.user.has_group(PRICE_GROUP)
        for rec in self:
            rec.amunet_price_visible = can_see


class ProductPricelistItemPV(models.Model):
    _inherit = 'product.pricelist.item'

    amunet_price_visible = fields.Boolean(compute='_compute_amunet_price_visible')

    @api.depends_context('uid')
    def _compute_amunet_price_visible(self):
        can_see = self.env.user.has_group(PRICE_GROUP)
        for rec in self:
            rec.amunet_price_visible = can_see


class PurchaseOrderFG(models.Model):
    _inherit = 'purchase.order'
    amount_untaxed = fields.Monetary(groups=PRICE_GROUP)
    amount_tax = fields.Monetary(groups=PRICE_GROUP)
    amount_total = fields.Monetary(groups=PRICE_GROUP)
    tax_totals = fields.Binary(groups=PRICE_GROUP)


class PurchaseOrderLineFG(models.Model):
    _inherit = 'purchase.order.line'
    price_unit = fields.Float(groups=PRICE_GROUP)
    price_subtotal = fields.Monetary(groups=PRICE_GROUP)
    price_total = fields.Monetary(groups=PRICE_GROUP)
    price_unit_product_uom = fields.Float(groups=PRICE_GROUP)
    discount = fields.Float(groups=PRICE_GROUP)


class PurchaseReportFG(models.Model):
    _inherit = 'purchase.report'
    price_total = fields.Float(groups=PRICE_GROUP)
    price_average = fields.Float(groups=PRICE_GROUP)


class StockLotFG(models.Model):
    _inherit = 'stock.lot'
    standard_price = fields.Float(groups=PRICE_GROUP)


class StockMoveFG(models.Model):
    _inherit = 'stock.move'
    price_unit = fields.Float(groups=PRICE_GROUP)


class AccountMoveFG(models.Model):
    _inherit = 'account.move'
    amount_untaxed = fields.Monetary(groups=PRICE_GROUP)
    amount_tax = fields.Monetary(groups=PRICE_GROUP)
    amount_total = fields.Monetary(groups=PRICE_GROUP)
    amount_total_in_currency_signed = fields.Monetary(groups=PRICE_GROUP)
    amount_untaxed_in_currency_signed = fields.Monetary(groups=PRICE_GROUP)
    tax_totals = fields.Binary(groups=PRICE_GROUP)


class AccountMoveLineFG(models.Model):
    _inherit = 'account.move.line'
    price_unit = fields.Float(groups=PRICE_GROUP)
    price_subtotal = fields.Monetary(groups=PRICE_GROUP)
    price_total = fields.Monetary(groups=PRICE_GROUP)
    discount = fields.Float(groups=PRICE_GROUP)
