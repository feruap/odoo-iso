# -*- coding: utf-8 -*-

from odoo import models
from odoo.exceptions import AccessError


PRICE_GROUP = 'amunet_price_visibility.group_price_viewer'


def _can_view_prices(recordset):
    return recordset.env.su or recordset.env.user.has_group(PRICE_GROUP)


def _blocked_fields(recordset, fields, sensitive_fields):
    """Devuelve los campos de precio que deben ocultarse para este usuario."""
    if _can_view_prices(recordset) or not sensitive_fields:
        return set()
    if fields is None:
        return set(sensitive_fields)
    return set(fields) & set(sensitive_fields)


def _check_price_export(recordset, fields, sensitive_fields):
    """Para exportaciones: sí lanza error si el usuario no tiene permiso."""
    if _can_view_prices(recordset):
        return
    blocked = sorted(set(fields or []) & set(sensitive_fields))
    if blocked:
        raise AccessError(
            'No tiene permisos para exportar campos de precio: %s' % ', '.join(blocked)
        )


def _mask_read(self, fields, sensitive_fields, load):
    """Lee el registro ocultando (como False) los campos de precio bloqueados."""
    blocked = _blocked_fields(self, fields, sensitive_fields)
    if not blocked:
        return super(type(self), self).read(fields=fields, load=load)
    safe_fields = None if fields is None else [f for f in fields if f not in blocked]
    results = super(type(self), self).read(fields=safe_fields, load=load)
    for record in results:
        for field in blocked:
            record[field] = False
    return results


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _amunet_price_fields = ('list_price', 'standard_price')

    def read(self, fields=None, load='_classic_read'):
        return _mask_read(self, fields, self._amunet_price_fields, load)

    def export_data(self, fields_to_export):
        _check_price_export(self, [f.split('/')[0] for f in fields_to_export or []], self._amunet_price_fields)
        return super().export_data(fields_to_export)


class ProductProduct(models.Model):
    _inherit = 'product.product'
    _amunet_price_fields = ('list_price', 'lst_price', 'standard_price')

    def read(self, fields=None, load='_classic_read'):
        return _mask_read(self, fields, self._amunet_price_fields, load)

    def export_data(self, fields_to_export):
        _check_price_export(self, [f.split('/')[0] for f in fields_to_export or []], self._amunet_price_fields)
        return super().export_data(fields_to_export)


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'
    _amunet_price_fields = ('price', 'discount')

    def read(self, fields=None, load='_classic_read'):
        return _mask_read(self, fields, self._amunet_price_fields, load)

    def export_data(self, fields_to_export):
        _check_price_export(self, [f.split('/')[0] for f in fields_to_export or []], self._amunet_price_fields)
        return super().export_data(fields_to_export)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _amunet_price_fields = ('amount_untaxed', 'amount_tax', 'amount_total', 'tax_totals')

    def read(self, fields=None, load='_classic_read'):
        return _mask_read(self, fields, self._amunet_price_fields, load)

    def export_data(self, fields_to_export):
        _check_price_export(self, [f.split('/')[0] for f in fields_to_export or []], self._amunet_price_fields)
        return super().export_data(fields_to_export)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _amunet_price_fields = (
        'price_unit',
        'price_subtotal',
        'price_total',
        'price_unit_product_uom',
        'discount',
    )

    def read(self, fields=None, load='_classic_read'):
        return _mask_read(self, fields, self._amunet_price_fields, load)

    def export_data(self, fields_to_export):
        _check_price_export(self, [f.split('/')[0] for f in fields_to_export or []], self._amunet_price_fields)
        return super().export_data(fields_to_export)


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'
    _amunet_price_fields = ('price_total', 'price_average')

    def read(self, fields=None, load='_classic_read'):
        return _mask_read(self, fields, self._amunet_price_fields, load)

    def export_data(self, fields_to_export):
        _check_price_export(self, [f.split('/')[0] for f in fields_to_export or []], self._amunet_price_fields)
        return super().export_data(fields_to_export)


class StockLot(models.Model):
    _inherit = 'stock.lot'
    _amunet_price_fields = ('standard_price',)

    def read(self, fields=None, load='_classic_read'):
        return _mask_read(self, fields, self._amunet_price_fields, load)

    def export_data(self, fields_to_export):
        _check_price_export(self, [f.split('/')[0] for f in fields_to_export or []], self._amunet_price_fields)
        return super().export_data(fields_to_export)


class StockMove(models.Model):
    _inherit = 'stock.move'
    _amunet_price_fields = ('price_unit', 'value', 'standard_price', 'remaining_value')

    def read(self, fields=None, load='_classic_read'):
        return _mask_read(self, fields, self._amunet_price_fields, load)

    def export_data(self, fields_to_export):
        _check_price_export(self, [f.split('/')[0] for f in fields_to_export or []], self._amunet_price_fields)
        return super().export_data(fields_to_export)


class AccountMove(models.Model):
    _inherit = 'account.move'
    _amunet_price_fields = (
        'amount_untaxed',
        'amount_tax',
        'amount_total',
        'amount_total_in_currency_signed',
        'amount_untaxed_in_currency_signed',
        'tax_totals',
    )

    def read(self, fields=None, load='_classic_read'):
        return _mask_read(self, fields, self._amunet_price_fields, load)

    def export_data(self, fields_to_export):
        _check_price_export(self, [f.split('/')[0] for f in fields_to_export or []], self._amunet_price_fields)
        return super().export_data(fields_to_export)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    _amunet_price_fields = (
        'price_unit',
        'price_subtotal',
        'price_total',
        'debit',
        'credit',
        'balance',
        'discount',
    )

    def read(self, fields=None, load='_classic_read'):
        return _mask_read(self, fields, self._amunet_price_fields, load)

    def export_data(self, fields_to_export):
        _check_price_export(self, [f.split('/')[0] for f in fields_to_export or []], self._amunet_price_fields)
        return super().export_data(fields_to_export)
