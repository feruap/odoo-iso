# -*- coding: utf-8 -*-
"""Candado ORM de precios (amunet_price_visibility).

Solo los miembros de "Amunet / Ver precios" pueden obtener un importe.

A diferencia de la version anterior (que sobreescribia ``read``), este
modulo se engancha en ``_read_format`` y ``_read_group``, que son los
metodos que la ORM de Odoo 19 usa REALMENTE por debajo de:

    read()  search_read()  web_read()  web_search_read()  read_group()

Sobreescribir solo ``read`` dejaba abierto ``search_read`` -- que es la
llamada que hacen las listas, los pivots, el exportador y cualquier
cliente XML-RPC / JSON-RPC. Por ahi se podia leer ``standard_price``
aunque la interfaz lo ocultara.

Cobertura:
  * _read_format -> lecturas de registro (interfaz, API, exportacion)
  * formatted_read_group / read_group -> agregados (pivot y grafico)
  * export_data  -> exportacion a CSV / XLSX
"""

from odoo import models
from odoo.exceptions import AccessError

PRICE_GROUP = 'amunet_price_visibility.group_price_viewer'


def _export_field_names(fields_to_export):
    return [f.split('/')[0] for f in fields_to_export or []]


def _aggregate_field(spec):
    """'amount_total:sum' -> 'amount_total'; '__count' -> ''."""
    return (spec or '').split(':')[0].split('.')[0]


class AmunetPriceMaskMixin:
    """Mixin de Python puro (no es un modelo) que enmascara importes.

    Se coloca ANTES de models.Model en la lista de bases para que su
    ``super()`` caiga en la clase del modelo de Odoo.
    """

    # Cada modelo declara aqui sus campos monetarios sensibles.
    _amunet_price_fields = ()

    def _amunet_can_view_prices(self):
        # env.su -> procesos internos del propio Odoo (calculos, contabilidad,
        # reportes que ya filtran por grupo). Un usuario nunca es su.
        return self.env.su or self.env.user.has_group(PRICE_GROUP)

    # -- lecturas de registro -------------------------------------------------
    def _read_format(self, fnames, load='_classic_read'):
        sensitive = set(self._amunet_price_fields)
        if not sensitive or self._amunet_can_view_prices():
            return super()._read_format(fnames, load=load)
        blocked = [f for f in (fnames or ()) if f in sensitive]
        if not blocked:
            return super()._read_format(fnames, load=load)
        safe = [f for f in fnames if f not in sensitive]
        result = super()._read_format(safe, load=load)
        for row in result:
            for fname in blocked:
                row[fname] = False
        return result

    # -- agregados (pivot, grafico, agrupar por) -----------------------------
    # Se bloquea SOLO en la capa publica (lo que llaman el navegador y los
    # clientes RPC). El metodo interno _read_group se deja intacto a
    # proposito: lo usan calculos internos de Odoo (conciliacion, valuacion,
    # reportes contables) que corren con el usuario en sesion, y romperlos
    # dejaria al almacen sin poder validar recepciones.
    def _amunet_check_aggregates(self, groupby, aggregates, having):
        sensitive = set(self._amunet_price_fields)
        if not sensitive or self._amunet_can_view_prices():
            return
        candidatos = set()
        for spec in list(groupby or ()) + list(aggregates or ()):
            candidatos.add(_aggregate_field(spec))
        for cond in (having or ()):
            if isinstance(cond, (list, tuple)) and cond:
                candidatos.add(_aggregate_field(cond[0]))
        blocked = sorted(candidatos & sensitive)
        if blocked:
            raise AccessError(
                'No tiene permisos para agrupar ni totalizar importes: %s'
                % ', '.join(blocked)
            )

    def formatted_read_group(self, domain, groupby=(), aggregates=(), having=(),
                             offset=0, limit=None, order=None):
        self._amunet_check_aggregates(groupby, aggregates, having)
        return super().formatted_read_group(
            domain, groupby=groupby, aggregates=aggregates, having=having,
            offset=offset, limit=limit, order=order,
        )

    def formatted_read_grouping_sets(self, domain, grouping_sets, aggregates=(), *, order=None):
        planos = [g for gs in (grouping_sets or ()) for g in (gs or ())]
        self._amunet_check_aggregates(planos, aggregates, ())
        return super().formatted_read_grouping_sets(
            domain, grouping_sets, aggregates=aggregates, order=order,
        )

    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        gb = [groupby] if isinstance(groupby, str) else list(groupby or ())
        self._amunet_check_aggregates(gb, fields, ())
        return super().read_group(
            domain, fields, groupby, offset=offset, limit=limit,
            orderby=orderby, lazy=lazy,
        )

    # -- exportacion ----------------------------------------------------------
    def export_data(self, fields_to_export):
        sensitive = set(self._amunet_price_fields)
        if sensitive and not self._amunet_can_view_prices():
            blocked = sorted(set(_export_field_names(fields_to_export)) & sensitive)
            if blocked:
                raise AccessError(
                    'No tiene permisos para exportar campos de precio: %s'
                    % ', '.join(blocked)
                )
        return super().export_data(fields_to_export)


class ProductTemplate(AmunetPriceMaskMixin, models.Model):
    _inherit = 'product.template'
    _amunet_price_fields = ('list_price', 'standard_price')


class ProductProduct(AmunetPriceMaskMixin, models.Model):
    _inherit = 'product.product'
    _amunet_price_fields = ('list_price', 'lst_price', 'standard_price')


class ProductSupplierinfo(AmunetPriceMaskMixin, models.Model):
    _inherit = 'product.supplierinfo'
    _amunet_price_fields = ('price', 'discount')


class PurchaseOrder(AmunetPriceMaskMixin, models.Model):
    _inherit = 'purchase.order'
    _amunet_price_fields = ('amount_untaxed', 'amount_tax', 'amount_total', 'tax_totals')


class PurchaseOrderLine(AmunetPriceMaskMixin, models.Model):
    _inherit = 'purchase.order.line'
    _amunet_price_fields = (
        'price_unit', 'price_subtotal', 'price_total', 'price_unit_product_uom', 'discount',
    )


class PurchaseReport(AmunetPriceMaskMixin, models.Model):
    _inherit = 'purchase.report'
    _amunet_price_fields = ('price_total', 'price_average')


class StockLot(AmunetPriceMaskMixin, models.Model):
    _inherit = 'stock.lot'
    _amunet_price_fields = ('standard_price',)


class StockMove(AmunetPriceMaskMixin, models.Model):
    _inherit = 'stock.move'
    _amunet_price_fields = ('price_unit', 'value', 'standard_price', 'remaining_value')


class AccountMove(AmunetPriceMaskMixin, models.Model):
    _inherit = 'account.move'
    _amunet_price_fields = (
        'amount_untaxed', 'amount_tax', 'amount_total',
        'amount_total_in_currency_signed', 'amount_untaxed_in_currency_signed', 'tax_totals',
    )


class AccountMoveLine(AmunetPriceMaskMixin, models.Model):
    _inherit = 'account.move.line'
    _amunet_price_fields = (
        'price_unit', 'price_subtotal', 'price_total',
        'debit', 'credit', 'balance', 'discount',
    )
