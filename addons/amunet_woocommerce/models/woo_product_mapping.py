# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AmunetWooProductMapping(models.Model):
    _name = 'amunet.woo.product.mapping'
    _description = 'Mapeo producto Odoo - WooCommerce'
    _order = 'woo_sku, id'
    _rec_name = 'woo_sku'

    backend_id = fields.Many2one(
        'amunet.woo.backend', string='Tienda', required=True,
        ondelete='cascade', index=True)
    product_id = fields.Many2one(
        'product.product', string='Producto Odoo', required=True, index=True)
    default_code = fields.Char(
        string='SKU Odoo', related='product_id.default_code', store=True)
    woo_product_id = fields.Integer(string='ID Woo', required=True)
    woo_parent_id = fields.Integer(
        string='ID padre Woo',
        help='0 para producto simple; ID del producto variable para variaciones.')
    woo_sku = fields.Char(string='SKU Woo')
    woo_name = fields.Char(string='Nombre en Woo')
    woo_type = fields.Char(string='Tipo Woo')
    sync_enabled = fields.Boolean(string='Sincronizar', default=True)
    last_pushed_qty = fields.Integer(string='Ultima cantidad publicada', readonly=True)
    last_sync_date = fields.Datetime(string='Ultimo envio', readonly=True)
    qty_to_push = fields.Integer(
        string='Cantidad actual Odoo', compute='_compute_qty_to_push')

    _sql_constraints = [
        ('uniq_backend_woo_item', 'unique(backend_id, woo_product_id, woo_parent_id)',
         'Este articulo de WooCommerce ya esta mapeado en esta tienda.'),
    ]

    def _compute_qty_to_push(self):
        for backend in self.mapped('backend_id'):
            records = self.filtered(lambda m: m.backend_id == backend)
            qty_map = backend._get_qty_for_products(records.mapped('product_id'))
            for mapping in records:
                mapping.qty_to_push = qty_map.get(mapping.product_id.id, 0)
        for mapping in self.filtered(lambda m: not m.backend_id):
            mapping.qty_to_push = 0

    @api.model
    def _upsert_from_woo(self, backend, woo_item, parent=None):
        """Crea o actualiza el mapeo de un articulo Woo emparejando por SKU.

        Regresa 'created', 'updated' o 'unmatched'.
        """
        woo_id = woo_item.get('id')
        parent_id = parent and parent.get('id') or 0
        values = {
            'woo_sku': woo_item.get('sku') or '',
            'woo_name': woo_item.get('name') or (parent and parent.get('name')) or '',
            'woo_type': woo_item.get('type') or ('variation' if parent else 'simple'),
        }
        existing = self.search([
            ('backend_id', '=', backend.id),
            ('woo_product_id', '=', woo_id),
            ('woo_parent_id', '=', parent_id),
        ], limit=1)
        if existing:
            existing.write(values)
            return 'updated'
        sku = (woo_item.get('sku') or '').strip()
        product = sku and self.env['product.product'].search(
            [('default_code', '=', sku)], limit=1)
        if not product:
            return 'unmatched'
        self.create(dict(values,
                         backend_id=backend.id,
                         product_id=product.id,
                         woo_product_id=woo_id,
                         woo_parent_id=parent_id))
        return 'created'
