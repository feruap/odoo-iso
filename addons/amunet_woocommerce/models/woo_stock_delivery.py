# -*- coding: utf-8 -*-

import hashlib

from odoo import api, fields, models, _


class AmunetWooStockDelivery(models.Model):
    """Registro inmutable de existencias publicadas de Odoo (APT) hacia Woo.

    Es el libro de idempotencia del camino de escritura: cada lote publicado
    a la tienda de pruebas deja aquí una fila con una huella única
    (``delivery_hash``). Antes de publicar un lote se consulta este ledger; si
    ya existe la huella, NO se vuelve a enviar (evita duplicar existencias en
    la tienda). No guarda credenciales ni secretos.
    """

    _name = 'amunet.woo.stock.delivery'
    _description = 'Publicación de existencias APT hacia WooCommerce'
    _order = 'id desc'

    backend_id = fields.Many2one(
        'amunet.woo.backend', string='Tienda',
        required=True, ondelete='restrict', index=True)
    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company, index=True)
    mapping_id = fields.Many2one(
        'amunet.woo.product.mapping', string='Mapeo',
        ondelete='set null', index=True)
    product_id = fields.Many2one(
        'product.product', string='Producto Odoo', ondelete='restrict')
    woo_product_id = fields.Integer(string='ID producto Woo')
    lot_id = fields.Many2one('stock.lot', string='Lote', ondelete='set null')
    lot_number = fields.Char(string='Número de lote')
    quantity = fields.Float(string='Piezas publicadas')
    expiration_month = fields.Integer(string='Mes de caducidad')
    expiration_year = fields.Integer(string='Año de caducidad')
    delivery_hash = fields.Char(
        string='Huella de publicación', required=True, index=True, copy=False)
    sync_log_id = fields.Many2one(
        'amunet.woo.sync.log', string='Bitácora', ondelete='set null')
    date = fields.Datetime(
        string='Fecha de publicación', default=fields.Datetime.now,
        required=True)
    state = fields.Selection([
        ('published', 'Publicado'),
        ('failed', 'Fallido'),
    ], string='Resultado', default='published', required=True)
    response_message = fields.Char(string='Respuesta de la tienda')

    _sql_constraints = [
        ('delivery_hash_uniq', 'unique(delivery_hash)',
         'La publicación de ese lote ya está registrada (idempotencia).'),
    ]

    @api.model
    def _build_hash(self, backend_id, woo_product_id, lot_number):
        """Huella única por (tienda, producto Woo, lote).

        No incluye la cantidad a propósito: el endpoint de la tienda AGREGA
        existencias, así que un lote se publica una sola vez aunque su
        cantidad cambie. Reenviarlo duplicaría el stock en la tienda.
        """
        raw = '%s|%s|%s' % (
            backend_id or 0, woo_product_id or 0, (lot_number or '').strip())
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    @api.model
    def _already_published(self, backend_id, woo_product_id, lot_number):
        digest = self._build_hash(backend_id, woo_product_id, lot_number)
        return self.search_count([
            ('delivery_hash', '=', digest),
            ('state', '=', 'published'),
        ]) > 0
