# -*- coding: utf-8 -*-
"""Bloqueo ORM de los importes comerciales.

Redefinir el campo con `groups=` hace que Odoo lo elimine del contexto del
usuario no autorizado: no aparece en vistas, no se puede exportar, no se puede
pedir por API y no se puede usar en filtros ni agrupaciones.

La lista cubre TODOS los campos de dinero de sale.order, sale.order.line y
sale.report, no solo los del total: `amount_to_invoice`, `price_reduce_*` o
`sale.report.price_unit` dejaban ver el precio por la puerta de atras.
"""
from odoo import fields, models

PRICE_GROUP = 'amunet_price_visibility.group_price_viewer'


class SaleOrderFG(models.Model):
    _inherit = 'sale.order'

    amount_untaxed = fields.Monetary(groups=PRICE_GROUP)
    amount_tax = fields.Monetary(groups=PRICE_GROUP)
    amount_total = fields.Monetary(groups=PRICE_GROUP)
    amount_invoiced = fields.Monetary(groups=PRICE_GROUP)
    amount_to_invoice = fields.Monetary(groups=PRICE_GROUP)
    amount_undiscounted = fields.Float(groups=PRICE_GROUP)
    amount_paid = fields.Float(groups=PRICE_GROUP)
    tax_totals = fields.Binary(groups=PRICE_GROUP)


class SaleOrderLineFG(models.Model):
    _inherit = 'sale.order.line'

    price_unit = fields.Float(groups=PRICE_GROUP)
    price_subtotal = fields.Monetary(groups=PRICE_GROUP)
    price_total = fields.Monetary(groups=PRICE_GROUP)
    price_tax = fields.Float(groups=PRICE_GROUP)
    discount = fields.Float(groups=PRICE_GROUP)
    price_reduce_taxexcl = fields.Monetary(groups=PRICE_GROUP)
    price_reduce_taxinc = fields.Monetary(groups=PRICE_GROUP)
    technical_price_unit = fields.Float(groups=PRICE_GROUP)
    amount_invoiced = fields.Monetary(groups=PRICE_GROUP)
    amount_to_invoice = fields.Monetary(groups=PRICE_GROUP)
    amount_to_invoice_at_date = fields.Float(groups=PRICE_GROUP)
    untaxed_amount_invoiced = fields.Monetary(groups=PRICE_GROUP)
    untaxed_amount_to_invoice = fields.Monetary(groups=PRICE_GROUP)


class SaleReportFG(models.Model):
    _inherit = 'sale.report'

    price_total = fields.Float(groups=PRICE_GROUP)
    price_subtotal = fields.Float(groups=PRICE_GROUP)
    price_unit = fields.Float(groups=PRICE_GROUP)
    discount = fields.Float(groups=PRICE_GROUP)
    discount_amount = fields.Monetary(groups=PRICE_GROUP)
    untaxed_amount_invoiced = fields.Monetary(groups=PRICE_GROUP)
    untaxed_amount_to_invoice = fields.Monetary(groups=PRICE_GROUP)
