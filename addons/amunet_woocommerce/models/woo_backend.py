# -*- coding: utf-8 -*-

import logging
import math

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

WOO_TIMEOUT = 30
WOO_BATCH_SIZE = 100


class AmunetWooBackend(models.Model):
    _name = 'amunet.woo.backend'
    _description = 'Tienda WooCommerce conectada'
    _inherit = ['mail.thread']
    _order = 'sequence, id'

    name = fields.Char(string='Nombre', required=True, tracking=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    environment = fields.Selection([
        ('staging', 'Staging (tst)'),
        ('production', 'Produccion (www)'),
    ], string='Entorno', required=True, default='staging', tracking=True)
    store_url = fields.Char(
        string='URL de la tienda',
        required=True,
        tracking=True,
        help='Ejemplo: https://tst.amunet.com.mx',
    )
    consumer_key = fields.Char(
        string='Consumer key',
        groups='amunet_woocommerce.group_woo_manager',
        help='Llave generada en WooCommerce: Ajustes > Avanzado > API REST.',
    )
    consumer_secret = fields.Char(
        string='Consumer secret',
        groups='amunet_woocommerce.group_woo_manager',
    )
    state = fields.Selection([
        ('draft', 'Sin probar'),
        ('connected', 'Conectada'),
        ('error', 'Error'),
    ], string='Estado', default='draft', required=True, tracking=True)
    connection_message = fields.Char(string='Ultimo resultado de conexion', readonly=True)

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Almacen origen',
        tracking=True,
        help='Almacen cuyas existencias se publican en WooCommerce. '
             'Vacio = existencias de toda la compania.',
    )
    stock_field = fields.Selection([
        ('free_qty', 'Disponible sin reservas (recomendado)'),
        ('qty_available', 'A la mano'),
        ('virtual_available', 'Pronosticado'),
    ], string='Cantidad a publicar', required=True, default='free_qty', tracking=True)
    auto_sync = fields.Boolean(
        string='Sincronizacion automatica',
        default=False,
        tracking=True,
        help='Si esta activo, el cron publica existencias periodicamente.',
    )
    last_sync_date = fields.Datetime(string='Ultima sincronizacion', readonly=True)

    mapping_ids = fields.One2many('amunet.woo.product.mapping', 'backend_id', string='Mapeos')
    mapping_count = fields.Integer(compute='_compute_counts')
    log_ids = fields.One2many('amunet.woo.sync.log', 'backend_id', string='Bitacora')
    log_count = fields.Integer(compute='_compute_counts')

    @api.depends('mapping_ids', 'log_ids')
    def _compute_counts(self):
        for backend in self:
            backend.mapping_count = len(backend.mapping_ids)
            backend.log_count = len(backend.log_ids)

    @api.constrains('store_url')
    def _check_store_url(self):
        for backend in self:
            url = (backend.store_url or '').strip()
            if not url.startswith('https://'):
                raise ValidationError(_('La URL de la tienda debe iniciar con https://'))

    # ------------------------------------------------------------------
    # Cliente API REST
    # ------------------------------------------------------------------

    def _wc_url(self, endpoint):
        self.ensure_one()
        base = (self.store_url or '').strip().rstrip('/')
        return '%s/wp-json/wc/v3/%s' % (base, endpoint.lstrip('/'))

    def _wc_request(self, method, endpoint, params=None, payload=None):
        """Llamada autenticada a la API REST de WooCommerce. Regresa (json, response)."""
        self.ensure_one()
        backend_sudo = self.sudo()
        if not backend_sudo.consumer_key or not backend_sudo.consumer_secret:
            raise UserError(_(
                'La tienda %s no tiene consumer key/secret configurados. '
                'Generalos en WooCommerce: Ajustes > Avanzado > API REST '
                '(permiso Lectura/Escritura).') % self.name)
        try:
            response = requests.request(
                method,
                self._wc_url(endpoint),
                params=params or {},
                json=payload,
                auth=(backend_sudo.consumer_key, backend_sudo.consumer_secret),
                timeout=WOO_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise UserError(_('No se pudo contactar la tienda %s: %s') % (self.store_url, exc))
        if response.status_code >= 400:
            detail = ''
            try:
                body = response.json()
                detail = body.get('message') or body.get('code') or ''
                if body.get('code') == 'rest_cannot_access':
                    detail += _(
                        ' (Un plugin de seguridad de WordPress esta bloqueando la '
                        'API REST para las llaves de WooCommerce; hay que permitir '
                        'el espacio de nombres wc/v3.)')
            except ValueError:
                detail = response.text[:200]
            raise UserError(_(
                'WooCommerce respondio %(code)s en %(endpoint)s: %(detail)s',
                code=response.status_code, endpoint=endpoint, detail=detail))
        try:
            return response.json(), response
        except ValueError:
            raise UserError(_('WooCommerce regreso una respuesta no valida (no es JSON).'))

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def action_test_connection(self):
        self.ensure_one()
        try:
            self._wc_request('GET', 'products', params={'per_page': 1})
        except UserError as exc:
            self.write({'state': 'error', 'connection_message': str(exc)[:500]})
            raise
        self.write({
            'state': 'connected',
            'connection_message': _('Conexion correcta (%s)') % fields.Datetime.now(),
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('WooCommerce'),
                'message': _('Conexion correcta con %s') % self.store_url,
            },
        }

    def action_import_products(self):
        """Descarga el catalogo de Woo y crea/actualiza mapeos por SKU."""
        self.ensure_one()
        log = self.env['amunet.woo.sync.log'].create({
            'backend_id': self.id,
            'operation': 'import',
        })
        created = updated = unmatched = 0
        messages = []
        Mapping = self.env['amunet.woo.product.mapping']
        page = 1
        while True:
            data, response = self._wc_request('GET', 'products', params={
                'per_page': WOO_BATCH_SIZE,
                'page': page,
                'status': 'publish',
            })
            if not data:
                break
            for woo_product in data:
                if woo_product.get('type') == 'variable':
                    variations = self._fetch_variations(woo_product['id'])
                    for variation in variations:
                        result = Mapping._upsert_from_woo(
                            self, variation, parent=woo_product)
                        created += result == 'created'
                        updated += result == 'updated'
                        if result == 'unmatched':
                            unmatched += 1
                            messages.append(_(
                                'Sin producto Odoo para SKU "%(sku)s" (%(name)s, variacion %(vid)s)',
                                sku=variation.get('sku') or '',
                                name=woo_product.get('name') or '',
                                vid=variation.get('id')))
                else:
                    result = Mapping._upsert_from_woo(self, woo_product)
                    created += result == 'created'
                    updated += result == 'updated'
                    if result == 'unmatched':
                        unmatched += 1
                        messages.append(_(
                            'Sin producto Odoo para SKU "%(sku)s" (%(name)s)',
                            sku=woo_product.get('sku') or '',
                            name=woo_product.get('name') or ''))
            total_pages = int(response.headers.get('X-WP-TotalPages') or 1)
            if page >= total_pages:
                break
            page += 1
        state = 'success' if not unmatched else 'partial'
        log.write({
            'state': state,
            'date_end': fields.Datetime.now(),
            'total_count': created + updated + unmatched,
            'done_count': created + updated,
            'failed_count': unmatched,
            'message': '\n'.join(messages) or _('Todos los SKU emparejados.'),
        })
        self.message_post(body=_(
            'Importacion de catalogo Woo: %(created)s mapeos nuevos, '
            '%(updated)s actualizados, %(unmatched)s SKU sin emparejar.',
            created=created, updated=updated, unmatched=unmatched))
        return log._action_open()

    def _fetch_variations(self, woo_product_id):
        variations = []
        page = 1
        while True:
            data, response = self._wc_request(
                'GET', 'products/%s/variations' % woo_product_id,
                params={'per_page': WOO_BATCH_SIZE, 'page': page})
            variations.extend(data)
            total_pages = int(response.headers.get('X-WP-TotalPages') or 1)
            if not data or page >= total_pages:
                break
            page += 1
        return variations

    def action_sync_stock(self):
        self.ensure_one()
        return self._sync_stock(force=True)

    def _get_qty_for_products(self, products):
        """Regresa {product_id: cantidad entera a publicar}."""
        self.ensure_one()
        ctx = {}
        if self.warehouse_id:
            ctx.update(warehouse=self.warehouse_id.id, warehouse_id=self.warehouse_id.id)
        products = products.with_context(**ctx)
        qty_map = {}
        for product in products:
            qty = product[self.stock_field] or 0.0
            qty_map[product.id] = max(int(math.floor(qty)), 0)
        return qty_map

    def _sync_stock(self, force=False):
        """Publica existencias en Woo. Con force publica todo; sin force solo cambios."""
        self.ensure_one()
        mappings = self.mapping_ids.filtered(
            lambda m: m.sync_enabled and m.product_id.active)
        if not mappings:
            raise UserError(_(
                'No hay mapeos activos. Usa "Importar catalogo Woo" primero.'))
        log = self.env['amunet.woo.sync.log'].create({
            'backend_id': self.id,
            'operation': 'stock',
        })
        qty_map = self._get_qty_for_products(mappings.mapped('product_id'))
        to_push = []
        for mapping in mappings:
            qty = qty_map.get(mapping.product_id.id, 0)
            if force or mapping.last_pushed_qty != qty or not mapping.last_sync_date:
                to_push.append((mapping, qty))
        done = failed = 0
        messages = []
        now = fields.Datetime.now()

        simple = [(m, q) for m, q in to_push if not m.woo_parent_id]
        variations = {}
        for mapping, qty in to_push:
            if mapping.woo_parent_id:
                variations.setdefault(mapping.woo_parent_id, []).append((mapping, qty))

        def push_batch(endpoint, batch):
            nonlocal done, failed
            payload = {'update': [{
                'id': m.woo_product_id,
                'manage_stock': True,
                'stock_quantity': q,
            } for m, q in batch]}
            try:
                data, _response = self._wc_request('POST', endpoint, payload=payload)
            except UserError as exc:
                failed += len(batch)
                messages.append(str(exc))
                return
            errors_by_id = {
                item.get('id'): item['error'].get('message', 'error')
                for item in data.get('update', []) if item.get('error')
            }
            for mapping, qty in batch:
                if mapping.woo_product_id in errors_by_id:
                    failed += 1
                    messages.append(_(
                        'SKU %(sku)s (Woo %(wid)s): %(error)s',
                        sku=mapping.woo_sku, wid=mapping.woo_product_id,
                        error=errors_by_id[mapping.woo_product_id]))
                else:
                    done += 1
                    mapping.write({'last_pushed_qty': qty, 'last_sync_date': now})

        for start in range(0, len(simple), WOO_BATCH_SIZE):
            push_batch('products/batch', simple[start:start + WOO_BATCH_SIZE])
        for parent_id, batch in variations.items():
            for start in range(0, len(batch), WOO_BATCH_SIZE):
                push_batch('products/%s/variations/batch' % parent_id,
                           batch[start:start + WOO_BATCH_SIZE])

        state = 'success' if not failed else ('partial' if done else 'error')
        log.write({
            'state': state,
            'date_end': fields.Datetime.now(),
            'total_count': len(to_push),
            'done_count': done,
            'failed_count': failed,
            'message': '\n'.join(messages) or _(
                '%(done)s productos publicados, %(skipped)s sin cambios.',
                done=done, skipped=len(mappings) - len(to_push)),
        })
        self.write({'last_sync_date': now})
        return log._action_open()

    @api.model
    def _cron_sync_stock(self):
        backends = self.search([('auto_sync', '=', True), ('state', '=', 'connected')])
        for backend in backends:
            try:
                backend._sync_stock(force=False)
                self.env.cr.commit()
            except Exception:
                _logger.exception(
                    'Fallo la sincronizacion automatica WooCommerce del backend %s',
                    backend.name)
                self.env.cr.rollback()

    def action_view_mappings(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'amunet_woocommerce.action_woo_product_mapping')
        action['domain'] = [('backend_id', '=', self.id)]
        action['context'] = {'default_backend_id': self.id}
        return action

    def action_view_logs(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'amunet_woocommerce.action_woo_sync_log')
        action['domain'] = [('backend_id', '=', self.id)]
        return action
