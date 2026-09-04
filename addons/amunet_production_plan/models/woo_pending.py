# -*- coding: utf-8 -*-
"""Pedidos de la tienda con material pendiente de surtir (vendido sin existencia).

La tienda deja pedir sin existencia cuando un agente compra como cliente
(mu-plugin amunet-agente-backorder) o en categorias sobre pedido. Lo que
falta queda en el pedido como meta:
  - por partida: _amunet_pendiente (unidades de venta = cajas)
  - por pedido:  _apt_fulfillment_needs {raiz_woo: piezas} (plugin APT)
Aqui se traen esos pedidos por la API de WooCommerce y se convierten a
PIEZAS por producto Odoo, para (a) que Almacen tenga la lista de lo que debe
surtir cuando salga lote, y (b) que el plan de produccion los sume como
demanda comprometida.
"""
import logging
import re
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)
ESTADOS_VIVOS = ('processing', 'on-hold')


class AmunetWooPendingLine(models.Model):
    _name = 'amunet.woo.pending.line'
    _description = 'Pedido Woo pendiente de surtir'
    _order = 'order_date asc, id'

    backend_id = fields.Many2one('amunet.woo.backend', string='Tienda', readonly=True)
    woo_order_id = fields.Integer(string='Pedido Woo', readonly=True, index=True)
    order_number = fields.Char(string='Pedido', readonly=True)
    order_date = fields.Datetime(string='Fecha del pedido', readonly=True)
    order_status = fields.Char(string='Estado Woo', readonly=True)
    customer = fields.Char(string='Cliente', readonly=True)
    agent_note = fields.Char(string='Agente / nota', readonly=True)
    woo_product_id = fields.Integer(string='Producto Woo', readonly=True)
    woo_variation_id = fields.Integer(string='Variacion Woo', readonly=True)
    woo_sku = fields.Char(string='SKU Woo', readonly=True)
    item_name = fields.Char(string='Partida', readonly=True)
    qty_ordered_units = fields.Float(string='Pedidas (cajas)', readonly=True)
    qty_pending_units = fields.Float(string='Pendientes (cajas)', readonly=True)
    pieces_per_unit = fields.Float(string='Piezas por caja', readonly=True, default=1.0)
    qty_pending = fields.Float(string='Piezas pendientes', readonly=True,
                               digits='Product Unit of Measure')
    mapping_id = fields.Many2one('amunet.woo.product.mapping', string='Mapeo', readonly=True)
    product_id = fields.Many2one('product.product', string='Producto Odoo', readonly=True, index=True)
    source = fields.Selection([('item', 'Partida (agente)'), ('apt', 'APT faltante')],
                              string='Origen', readonly=True)
    note = fields.Char(string='Observacion', readonly=True)
    fetched_at = fields.Datetime(string='Leido de la tienda', readonly=True)

    # ------------------------------------------------------------------
    @staticmethod
    def _pieces_from_sku(sku):
        """DMTOR02.20 -> 20 ; DMCAP01.05 -> 5 ; DMTOR02.20-1 -> 20 ; sin punto -> 1."""
        m = re.search(r'\.(\d+)', sku or '')
        try:
            n = float(m.group(1)) if m else 1.0
        except ValueError:
            n = 1.0
        return n if n > 0 else 1.0

    @staticmethod
    def _meta(obj, key, default=None):
        for m in (obj or {}).get('meta_data') or []:
            if m.get('key') == key:
                return m.get('value')
        return default

    def _mapping_for(self, woo_ids, sku=None):
        Map = self.env['amunet.woo.product.mapping'].sudo()
        for wid in woo_ids:
            if not wid:
                continue
            mp = Map.search([('woo_product_id', '=', int(wid)), ('product_id', '!=', False)], limit=1)
            if mp:
                return mp
        if sku:
            raiz = re.split(r'[.\-]', sku)[0]
            if raiz:
                mp = Map.search([('woo_sku', '=', raiz), ('product_id', '!=', False)], limit=1)
                if mp:
                    return mp
                prod = self.env['product.product'].sudo().search([('default_code', '=', raiz)], limit=1)
                if prod:
                    mp = Map.search([('product_id', '=', prod.id)], limit=1)
                    return mp or Map  # puede venir vacio; el producto se resuelve aparte
        return Map

    _woo_prod_cache = {}

    def _woo_product(self, backend, woo_id):
        key = (backend.id, int(woo_id))
        if key not in self._woo_prod_cache:
            try:
                data, _r = backend._wc_get('products/%d' % int(woo_id))
            except Exception as e:  # noqa
                _logger.warning('No se pudo leer el producto Woo %s: %s', woo_id, e)
                data = {}
            self._woo_prod_cache[key] = data if isinstance(data, dict) else {}
        return self._woo_prod_cache[key]

    def _sku_of_woo_product(self, backend, woo_id):
        return (self._woo_product(backend, woo_id) or {}).get('sku') or ''

    def _name_of_woo_product(self, backend, woo_id):
        return (self._woo_product(backend, woo_id) or {}).get('name') or ''

    @api.model
    def action_fetch(self):
        """Reemplaza la lista con lo que hoy tiene la tienda pendiente."""
        backend = self.env['amunet.woo.backend'].sudo().search([('active', '=', True)], limit=1)
        if not backend:
            _logger.warning('amunet.woo.pending.line: no hay tienda configurada')
            return False
        ahora = fields.Datetime.now()
        vals_list = []
        page = 1
        while True:
            try:
                data, _resp = backend._wc_get('orders', {
                    'status': ','.join(ESTADOS_VIVOS), 'per_page': 100, 'page': page,
                    'orderby': 'date', 'order': 'asc'})
            except Exception as e:  # noqa
                _logger.error('No se pudieron leer pedidos de la tienda: %s', e)
                break
            if not isinstance(data, list) or not data:
                break
            for order in data:
                vals_list.extend(self._vals_from_order(backend, order, ahora))
            if len(data) < 100:
                break
            page += 1
        self.sudo().search([]).unlink()
        if vals_list:
            self.sudo().create(vals_list)
        _logger.info('Pedidos pendientes de surtir: %s partidas', len(vals_list))
        return True

    def _vals_from_order(self, backend, order, ahora):
        out = []
        billing = order.get('billing') or {}
        customer = ('%s %s' % (billing.get('first_name', ''), billing.get('last_name', ''))).strip() \
            or (billing.get('company') or '')
        if billing.get('company') and billing.get('company') not in customer:
            customer = '%s (%s)' % (customer, billing['company']) if customer else billing['company']
        base = {
            'backend_id': backend.id,
            'woo_order_id': int(order.get('id') or 0),
            'order_number': str(order.get('number') or order.get('id')),
            'order_date': (order.get('date_created_gmt') or '').replace('T', ' ')[:19] or False,
            'order_status': order.get('status'),
            'customer': customer,
            'agent_note': self._meta(order, 'salesking_agent_name') or self._meta(order, '_salesking_agent_id') or '',
            'fetched_at': ahora,
        }
        cubiertos = set()
        # (a) partidas con pendiente marcado por el mu-plugin de agentes
        for item in order.get('line_items') or []:
            pend = self._meta(item, '_amunet_pendiente')
            try:
                pend = float(pend or 0)
            except (TypeError, ValueError):
                pend = 0.0
            if pend <= 0:
                continue
            sku = item.get('sku') or ''
            ppu = self._pieces_from_sku(sku)
            mp = self._mapping_for([item.get('variation_id'), item.get('product_id')], sku)
            prod = mp.product_id if mp else self.env['product.product']
            if not prod and sku:
                prod = self.env['product.product'].sudo().search(
                    [('default_code', '=', re.split(r'[.\-]', sku)[0])], limit=1)
            out.append(dict(base, **{
                'woo_product_id': int(item.get('product_id') or 0),
                'woo_variation_id': int(item.get('variation_id') or 0),
                'woo_sku': sku,
                'item_name': item.get('name'),
                'qty_ordered_units': float(item.get('quantity') or 0),
                'qty_pending_units': pend,
                'pieces_per_unit': ppu,
                'qty_pending': pend * ppu,
                'mapping_id': mp.id if mp else False,
                'product_id': prod.id if prod else False,
                'source': 'item',
                'note': '' if prod else _('Sin producto Odoo para SKU %s') % sku,
            }))
            cubiertos.add(int(item.get('product_id') or 0))
        # (b) faltante que registro el APT por raiz (pedidos anteriores al mu-plugin)
        needs = self._meta(order, '_apt_fulfillment_needs')
        if isinstance(needs, dict) and not out:
            for raw_id, piezas in needs.items():
                try:
                    piezas = float(piezas or 0)
                except (TypeError, ValueError):
                    piezas = 0.0
                if piezas <= 0:
                    continue
                sku_raw = self._sku_of_woo_product(backend, raw_id)
                mp = self._mapping_for([raw_id], sku_raw)
                prod = mp.product_id if mp else self.env['product.product']
                if not prod and sku_raw:
                    prod = self.env['product.product'].sudo().search(
                        [('default_code', '=', re.split(r'[.\-]', sku_raw)[0])], limit=1)
                out.append(dict(base, **{
                    'woo_product_id': int(raw_id),
                    'woo_sku': sku_raw or (mp.woo_sku if mp else ''),
                    'item_name': (mp.woo_name if mp else '') or self._name_of_woo_product(backend, raw_id) or _('Raiz Woo %s') % raw_id,
                    'qty_pending_units': 0.0,
                    'pieces_per_unit': 1.0,
                    'qty_pending': piezas,
                    'mapping_id': mp.id if mp else False,
                    'product_id': prod.id if prod else False,
                    'source': 'apt',
                    'note': '' if prod else _('Raiz Woo %s sin mapeo en Odoo: asignar en 1109') % raw_id,
                }))
        return out

    @api.model
    def pending_by_product(self):
        """{product_id: piezas pendientes} de pedidos vivos, para el plan."""
        res = {}
        for line in self.sudo().search([('product_id', '!=', False),
                                        ('order_status', 'in', ESTADOS_VIVOS)]):
            res[line.product_id.id] = res.get(line.product_id.id, 0.0) + line.qty_pending
        return res

    @api.model
    def cron_fetch(self):
        self.action_fetch()
