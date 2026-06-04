# -*- coding: utf-8 -*-
"""
Redefine fields de precio con groups= a nivel field (no solo en vistas).

El override de read()/export_data() en price_security.py solo bloquea cuando
se invoca explicitamente el API publico (read([fields]) o export). Cuando
alguien accede record.amount_total via attribute Python (lo que pasa en
computados, reportes generados, getters, etc), Odoo usa _read() privado y
salta el guardrail.

La via cuanonica de Odoo: redefinir el campo con groups=. Odoo entonces NO
incluye el campo en los resultados para usuarios fuera del grupo, en CUALQUIER
ruta de acceso (incluyendo property access y search/group_by).

Mantenemos los overrides de read() como segunda capa.
"""
from odoo import models, fields

PRICE_GROUP = 'amunet_price_visibility.group_price_viewer'


class ProductTemplateFG(models.Model):
    _inherit = 'product.template'
    list_price = fields.Float(groups=PRICE_GROUP)
    standard_price = fields.Float(groups=PRICE_GROUP)


class ProductProductFG(models.Model):
    _inherit = 'product.product'
    lst_price = fields.Float(groups=PRICE_GROUP)
    standard_price = fields.Float(groups=PRICE_GROUP)


class ProductSupplierinfoFG(models.Model):
    _inherit = 'product.supplierinfo'
    price = fields.Float(groups=PRICE_GROUP)
    discount = fields.Float(groups=PRICE_GROUP)


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
