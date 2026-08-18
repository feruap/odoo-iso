# -*- coding: utf-8 -*-
"""Cinturon y tirantes: enmascara read() y bloquea export_data().

Mismo patron que amunet_price_visibility.price_security, para que un cliente
externo (XML-RPC, exportacion CSV) tampoco pueda sacar los importes.
"""
from odoo import models
from odoo.exceptions import AccessError

PRICE_GROUP = 'amunet_price_visibility.group_price_viewer'


def _can_view(recordset):
    return recordset.env.su or recordset.env.user.has_group(PRICE_GROUP)


def _blocked(recordset, requested, sensitive):
    if _can_view(recordset) or not sensitive:
        return set()
    if requested is None:
        return set(sensitive)
    return set(requested) & set(sensitive)


def _mask(results, blocked):
    for record in results:
        for name in blocked:
            record[name] = False
    return results


def _check_export(recordset, names, sensitive):
    if _can_view(recordset):
        return
    denied = sorted(set(names or []) & set(sensitive))
    if denied:
        raise AccessError(
            'No tiene permisos para exportar importes de venta: %s' % ', '.join(denied))


def _names(fields_to_export):
    return [f.split('/')[0] for f in fields_to_export or []]


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _amunet_sale_fields = (
        'amount_untaxed', 'amount_tax', 'amount_total', 'tax_totals',
        'amount_invoiced', 'amount_to_invoice', 'amount_undiscounted',
        'amount_paid')

    def read(self, fields=None, load='_classic_read'):
        blocked = _blocked(self, fields, self._amunet_sale_fields)
        if not blocked:
            return super().read(fields=fields, load=load)
        safe = None if fields is None else [f for f in fields if f not in blocked]
        return _mask(super().read(fields=safe, load=load), blocked)

    def export_data(self, fields_to_export):
        _check_export(self, _names(fields_to_export), self._amunet_sale_fields)
        return super().export_data(fields_to_export)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _amunet_sale_fields = (
        'price_unit', 'price_subtotal', 'price_total', 'price_tax', 'discount',
        'price_reduce_taxexcl', 'price_reduce_taxinc', 'technical_price_unit',
        'amount_invoiced', 'amount_to_invoice', 'amount_to_invoice_at_date',
        'untaxed_amount_invoiced', 'untaxed_amount_to_invoice')

    def read(self, fields=None, load='_classic_read'):
        blocked = _blocked(self, fields, self._amunet_sale_fields)
        if not blocked:
            return super().read(fields=fields, load=load)
        safe = None if fields is None else [f for f in fields if f not in blocked]
        return _mask(super().read(fields=safe, load=load), blocked)

    def export_data(self, fields_to_export):
        _check_export(self, _names(fields_to_export), self._amunet_sale_fields)
        return super().export_data(fields_to_export)


class SaleReport(models.Model):
    _inherit = 'sale.report'
    _amunet_sale_fields = (
        'price_total', 'price_subtotal', 'price_unit', 'discount',
        'discount_amount', 'untaxed_amount_invoiced', 'untaxed_amount_to_invoice')

    def read(self, fields=None, load='_classic_read'):
        blocked = _blocked(self, fields, self._amunet_sale_fields)
        if not blocked:
            return super().read(fields=fields, load=load)
        safe = None if fields is None else [f for f in fields if f not in blocked]
        return _mask(super().read(fields=safe, load=load), blocked)

    def export_data(self, fields_to_export):
        _check_export(self, _names(fields_to_export), self._amunet_sale_fields)
        return super().export_data(fields_to_export)
