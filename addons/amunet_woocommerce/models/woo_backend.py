# -*- coding: utf-8 -*-

import hashlib
import hmac
import json
import logging
import time

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

WOO_TIMEOUT = 30
WOO_BATCH_SIZE = 100
# Límite duro de páginas por corrida: la paginación siempre está acotada.
WOO_MAX_PAGES = 50


class AmunetWooBackend(models.Model):
    """Conexión con WooCommerce.

    La lectura del catálogo siempre usa la API REST de WooCommerce. La
    escritura es deliberadamente puntual y manual: únicamente nombres e
    imágenes iniciados desde un mapeo revisado. Nunca publica existencias ni
    altera pedidos.
    """

    _name = 'amunet.woo.backend'
    _description = 'Tienda WooCommerce (solo lectura)'
    _inherit = ['mail.thread']
    _order = 'sequence, id'

    name = fields.Char(string='Nombre', required=True, tracking=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company, index=True)
    store_url = fields.Char(
        string='URL de la tienda',
        required=True,
        tracking=True,
        help='Ejemplo: https://tst.amunet.com.mx',
    )
    consumer_key = fields.Char(
        string='Consumer key',
        groups='amunet_woocommerce.group_woo_admin',
        help='Llave de solo lectura generada en WooCommerce: '
             'Ajustes > Avanzado > API REST.',
    )
    consumer_secret = fields.Char(
        string='Consumer secret',
        groups='amunet_woocommerce.group_woo_admin',
    )
    allow_manual_writes = fields.Boolean(
        string='Permitir actualizar nombres e imágenes en Woo',
        default=False,
        groups='amunet_woocommerce.group_woo_admin',
        help='Requiere una API key WooCommerce con permiso Lectura/Escritura. '
             'No habilita sincronización automática de inventario.')
    wp_media_user = fields.Char(
        string='Usuario WordPress para medios',
        groups='amunet_woocommerce.group_woo_admin',
        help='Usuario de WordPress con Application Password para subir una '
             'fotografía desde Odoo hacia WooCommerce.')
    wp_media_app_password = fields.Char(
        string='Application Password WordPress',
        groups='amunet_woocommerce.group_woo_admin',
        help='Contraseña de aplicación, no la contraseña normal de WordPress.')
    bridge_secret = fields.Char(
        string='Secreto puente Odoo - Woo',
        groups='amunet_woocommerce.group_woo_admin',
        copy=False,
        help='Secreto HMAC configurado por el administrador técnico en ambos '
             'servidores. Permite las acciones manuales de nombre y fotografía.')
    # --- Publicación de existencias APT -> tienda de PRUEBAS (FASE 1) ---
    allow_stock_publish = fields.Boolean(
        string='Permitir publicar existencias a la tienda',
        default=False,
        groups='amunet_woocommerce.group_woo_admin',
        help='Candado independiente del de nombres/imágenes. Al activarlo se '
             'permite PUBLICAR existencias de producto terminado (APT, por '
             'pieza, solo lotes liberados) hacia la tienda. Debe usarse solo '
             'contra la tienda de pruebas (tst.amunet.com.mx).')
    apt_pieces_location_id = fields.Many2one(
        'stock.location',
        string='Ubicación APT de piezas',
        groups='amunet_woocommerce.group_woo_admin',
        help='Ubicación de existencias en piezas a publicar '
             '(APT/Existencias_Presentación 1 pieza). Si se deja vacía, se '
             'busca por nombre dentro de la compañía.')
    apt_wp_user = fields.Char(
        string='Usuario WordPress para publicar existencias',
        groups='amunet_woocommerce.group_woo_admin',
        help='Usuario de WordPress con rol acotado y Application Password '
             'dedicado para el endpoint apt/v1/inventory/deliver. Lo crea '
             'Fernando cuando se vaya a probar; nunca la contraseña normal.')
    apt_wp_app_password = fields.Char(
        string='Application Password (publicar existencias)',
        groups='amunet_woocommerce.group_woo_admin',
        copy=False,
        help='Contraseña de aplicación dedicada para publicar existencias. '
             'No es la contraseña normal de WordPress.')
    state = fields.Selection([
        ('draft', 'Sin probar'),
        ('connected', 'Conectada'),
        ('error', 'Error'),
    ], string='Estado', default='draft', required=True, tracking=True)
    connection_message = fields.Char(string='Último resultado de conexión', readonly=True)
    last_read_date = fields.Datetime(string='Última lectura GET', readonly=True)

    mapping_ids = fields.One2many('amunet.woo.product.mapping', 'backend_id', string='Mapeos')
    mapping_count = fields.Integer(compute='_compute_counts')
    log_ids = fields.One2many('amunet.woo.sync.log', 'backend_id', string='Bitácora')
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
    # Cliente API REST (solo lectura)
    # ------------------------------------------------------------------

    def _wc_url(self, endpoint):
        self.ensure_one()
        base = (self.store_url or '').strip().rstrip('/')
        return '%s/wp-json/wc/v3/%s' % (base, endpoint.lstrip('/'))

    def _wc_get(self, endpoint, params=None):
        """Llamada GET autenticada a la API REST de WooCommerce.

        Es la ÚNICA operación HTTP del módulo: jamás se escribe en la tienda.
        Regresa (json, response). La bitácora nunca registra credenciales.
        """
        self.ensure_one()
        if not self.consumer_key or not self.consumer_secret:
            raise UserError(_(
                'La tienda %s no tiene consumer key/secret configurados. '
                'Genéralos en WooCommerce: Ajustes > Avanzado > API REST '
                '(permiso de solo Lectura).') % self.name)
        try:
            response = requests.get(
                self._wc_url(endpoint),
                params=params or {},
                auth=(self.consumer_key, self.consumer_secret),
                timeout=WOO_TIMEOUT,
                verify=True,
            )
        except requests.RequestException as exc:
            raise UserError(
                _('No se pudo contactar la tienda %s: %s') % (self.store_url, exc))
        if response.status_code >= 400:
            detail = ''
            try:
                body = response.json()
                detail = body.get('message') or body.get('code') or ''
                if body.get('code') == 'rest_cannot_access':
                    detail += _(
                        ' (Un plugin de seguridad de WordPress está bloqueando la '
                        'API REST para las llaves de WooCommerce; hay que permitir '
                        'el espacio de nombres wc/v3.)')
            except ValueError:
                detail = response.text[:200]
            raise UserError(_(
                'WooCommerce respondió %(code)s en %(endpoint)s: %(detail)s',
                code=response.status_code, endpoint=endpoint, detail=detail))
        try:
            return response.json(), response
        except ValueError:
            raise UserError(_('WooCommerce regresó una respuesta no válida (no es JSON).'))

    def _wc_put(self, endpoint, payload):
        """Actualización manual y auditada de un producto/variación Woo."""
        self.ensure_one()
        if not self.allow_manual_writes:
            raise UserError(_(
                'La tienda no está autorizada para escritura manual. Un '
                'administrador debe activar "Permitir actualizar nombres e '
                'imágenes en Woo" y configurar una API key Lectura/Escritura.'))
        if not self.consumer_key or not self.consumer_secret:
            raise UserError(_('La tienda no tiene credenciales de API configuradas.'))
        try:
            response = requests.put(
                self._wc_url(endpoint), json=payload,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=WOO_TIMEOUT, verify=True,
            )
        except requests.RequestException as exc:
            raise UserError(_('No se pudo actualizar WooCommerce: %s') % exc)
        if response.status_code >= 400:
            try:
                detail = response.json().get('message') or response.text[:200]
            except ValueError:
                detail = response.text[:200]
            raise UserError(_('WooCommerce rechazó la actualización (%(code)s): %(detail)s') % {
                'code': response.status_code, 'detail': detail})
        try:
            return response.json()
        except ValueError:
            raise UserError(_('WooCommerce no regresó JSON al actualizar el producto.'))

    def _wp_upload_media(self, image_bytes, filename):
        """Sube un binario a la biblioteca WordPress y devuelve su URL pública."""
        self.ensure_one()
        if not self.allow_manual_writes:
            raise UserError(_('La escritura manual hacia WooCommerce no está habilitada.'))
        if not self.wp_media_user or not self.wp_media_app_password:
            raise UserError(_(
                'Para transferir una foto de Odoo a Woo configura el usuario '
                'WordPress y su Application Password en la tienda.'))
        url = '%s/wp-json/wp/v2/media' % (self.store_url or '').rstrip('/')
        try:
            response = requests.post(
                url, data=image_bytes,
                headers={
                    'Content-Disposition': 'attachment; filename="%s"' % filename,
                    'Content-Type': 'image/png',
                },
                auth=(self.wp_media_user, self.wp_media_app_password),
                timeout=WOO_TIMEOUT, verify=True,
            )
        except requests.RequestException as exc:
            raise UserError(_('No se pudo subir la foto a WordPress: %s') % exc)
        if response.status_code >= 400:
            try:
                detail = response.json().get('message') or response.text[:200]
            except ValueError:
                detail = response.text[:200]
            raise UserError(_('WordPress rechazó la fotografía (%(code)s): %(detail)s') % {
                'code': response.status_code, 'detail': detail})
        try:
            source_url = response.json().get('source_url')
        except ValueError:
            source_url = False
        if not source_url:
            raise UserError(_('WordPress no devolvió la URL de la fotografía subida.'))
        return source_url

    def _bridge_request(self, method, endpoint, payload=None):
        """Llama al puente instalado en WordPress para edición manual.

        El puente evita depender de un usuario WordPress, de una contraseña
        personal o de una API key Woo de escritura. Cada petición lleva una
        firma HMAC y solo realiza la acción solicitada desde un mapeo.
        """
        self.ensure_one()
        if not self.bridge_secret:
            raise UserError(_(
                'El puente Odoo - Woo no está configurado para esta tienda.'))
        raw = json.dumps(payload or {}, separators=(',', ':')).encode('utf-8')
        timestamp = str(int(time.time()))
        message = timestamp.encode('utf-8') + b'.' + raw
        signature = hmac.new(
            self.bridge_secret.encode('utf-8'), message, hashlib.sha256
        ).hexdigest()
        url = '%s/wp-json/amunet-odoo/v1/%s' % (
            (self.store_url or '').rstrip('/'), endpoint.lstrip('/'))
        try:
            response = requests.request(
                method, url, data=raw,
                headers={
                    'Content-Type': 'application/json',
                    'X-Amunet-Timestamp': timestamp,
                    'X-Amunet-Signature': signature,
                }, timeout=WOO_TIMEOUT, verify=True,
            )
        except requests.RequestException as exc:
            raise UserError(_('No se pudo comunicar con el puente Woo: %s') % exc)
        if response.status_code >= 400:
            try:
                detail = response.json().get('message') or response.text[:300]
            except ValueError:
                detail = response.text[:300]
            raise UserError(_('El puente Woo rechazó la operación (%(code)s): %(detail)s') % {
                'code': response.status_code, 'detail': detail})
        try:
            return response.json()
        except ValueError:
            raise UserError(_('El puente Woo no devolvió una respuesta válida.'))

    def _bounded_total_pages(self, response):
        """Normaliza la paginación de Woo sin propagar encabezados inválidos."""
        raw_value = response.headers.get('X-WP-TotalPages') or 1
        try:
            total_pages = int(raw_value)
        except (TypeError, ValueError):
            _logger.warning(
                'WooCommerce devolvió X-WP-TotalPages inválido: %r. '
                'Se tratará como una sola página.',
                raw_value,
            )
            total_pages = 1
        return min(max(total_pages, 1), WOO_MAX_PAGES)

    # ------------------------------------------------------------------
    # Publicación de existencias APT -> tienda (FASE 1, tras candado)
    # ------------------------------------------------------------------

    def _apt_pieces_location(self):
        """Ubicación de existencias en piezas de APT para esta tienda.

        Usa la configurada explícitamente; si no hay, la busca por nombre
        dentro de la compañía. Devuelve un recordset (vacío si no se halla).
        """
        self.ensure_one()
        if self.apt_pieces_location_id:
            return self.apt_pieces_location_id
        return self.env['stock.location'].search([
            ('complete_name', 'ilike', 'APT/Existencias_Presentación 1 pieza'),
            ('company_id', 'in', (self.company_id.id, False)),
        ], limit=1)

    def _read_released_piece_stock(self, mapping):
        """Existencias en piezas por lote LIBERADO para un mapeo.

        Devuelve una lista de dicts por lote:
        ``{lot, lot_number, quantity, expiration_month, expiration_year}``.
        Solo lotes con ``amunet_lot_release_state == 'released'`` y con
        cantidad disponible (libre) > 0. Nunca incluye lotes pendientes o
        retenidos por calidad.
        """
        self.ensure_one()
        Lot = self.env['stock.lot']
        if 'amunet_lot_release_state' not in Lot._fields:
            return []
        location = self._apt_pieces_location()
        if not mapping.product_id or not location:
            return []
        quants = self.env['stock.quant'].search([
            ('product_id', '=', mapping.product_id.id),
            ('location_id', 'child_of', location.id),
            ('company_id', '=', self.company_id.id),
        ])
        by_lot = {}
        for quant in quants:
            lot = quant.lot_id
            if not lot or lot.amunet_lot_release_state != 'released':
                continue
            reserved = getattr(quant, 'reserved_quantity', 0.0)
            free = quant.quantity - reserved
            if free <= 0:
                continue
            by_lot.setdefault(lot, 0.0)
            by_lot[lot] += free
        results = []
        for lot, qty in by_lot.items():
            month = year = False
            if lot.expiration_date:
                month = lot.expiration_date.month
                year = lot.expiration_date.year
            results.append({
                'lot': lot,
                'lot_number': lot.name,
                'quantity': qty,
                'expiration_month': month,
                'expiration_year': year,
            })
        return results

    def _apt_deliver(self, payload):
        """POST autenticado al endpoint de existencias del plugin AlmacenPT.

        Endpoint: ``POST {store}/wp-json/apt/v1/inventory/deliver`` (crea/agrega
        existencias por pieza). Va tras el candado ``allow_stock_publish`` y se
        autentica con el Application Password dedicado de la tienda. La bitácora
        nunca registra credenciales.

        NOTA (a confirmar con Fernando al aprovisionar credenciales): AlmacenPT
        usa Application Password; si se decide enrutar por el puente HMAC
        (amunet-odoo/v1), aquí se cambia el mecanismo de autenticación.
        """
        self.ensure_one()
        if not self.allow_stock_publish:
            raise UserError(_(
                'La publicación de existencias no está habilitada para esta '
                'tienda. Un administrador debe activar "Permitir publicar '
                'existencias a la tienda" (solo contra la tienda de pruebas).'))
        if not self.apt_wp_user or not self.apt_wp_app_password:
            raise UserError(_(
                'Falta el usuario WordPress y su Application Password dedicado '
                'para publicar existencias (los provee Fernando).'))
        url = '%s/wp-json/apt/v1/inventory/deliver' % (
            (self.store_url or '').strip().rstrip('/'))
        try:
            response = requests.post(
                url, json=payload,
                auth=(self.apt_wp_user, self.apt_wp_app_password),
                timeout=WOO_TIMEOUT, verify=True,
            )
        except requests.RequestException as exc:
            raise UserError(_('No se pudo publicar en la tienda: %s') % exc)
        if response.status_code >= 400:
            try:
                detail = response.json().get('message') or response.text[:300]
            except ValueError:
                detail = response.text[:300]
            raise UserError(_(
                'La tienda rechazó la publicación (%(code)s): %(detail)s') % {
                'code': response.status_code, 'detail': detail})
        try:
            return response.json()
        except ValueError:
            return {}

    def action_publish_stock(self):
        """Publica a la tienda las existencias liberadas de los mapeos confirmados.

        Idempotente: un lote ya publicado no se reenvía (ledger
        ``amunet.woo.stock.delivery``). Deja bitácora en ``woo_sync_log``.
        """
        self.ensure_one()
        if not self.allow_stock_publish:
            raise UserError(_(
                'La publicación de existencias no está habilitada para esta '
                'tienda.'))
        Delivery = self.env['amunet.woo.stock.delivery']
        mappings = self.env['amunet.woo.product.mapping'].search([
            ('backend_id', '=', self.id),
            ('relation_state', '=', 'confirmed'),
            ('product_id', '!=', False),
        ])
        published = skipped = failed = 0
        messages = []
        for mapping in mappings:
            woo_pid = mapping.woo_product_id
            for lot_data in self._read_released_piece_stock(mapping):
                lot_number = lot_data['lot_number']
                if Delivery._already_published(self.id, woo_pid, lot_number):
                    skipped += 1
                    continue
                payload = {
                    'product_id': woo_pid,
                    'quantity': lot_data['quantity'],
                    'expiration_month': lot_data['expiration_month'],
                    'expiration_year': lot_data['expiration_year'],
                    'lot_number': lot_number,
                    'notes': 'Publicado desde Odoo APT (mapeo %s)' % mapping.id,
                }
                digest = Delivery._build_hash(self.id, woo_pid, lot_number)
                try:
                    result = self._apt_deliver(payload)
                except UserError as exc:
                    failed += 1
                    messages.append(_('Lote %(lot)s (%(sku)s): %(err)s', lot=lot_number,
                                      sku=mapping.woo_sku or '', err=str(exc)))
                    Delivery.create({
                        'backend_id': self.id,
                        'company_id': self.company_id.id,
                        'mapping_id': mapping.id,
                        'product_id': mapping.product_id.id,
                        'woo_product_id': woo_pid,
                        'lot_id': lot_data['lot'].id,
                        'lot_number': lot_number,
                        'quantity': lot_data['quantity'],
                        'expiration_month': lot_data['expiration_month'] or 0,
                        'expiration_year': lot_data['expiration_year'] or 0,
                        'delivery_hash': '%s-failed-%s' % (digest, mapping.id),
                        'state': 'failed',
                        'response_message': str(exc)[:200],
                    })
                    continue
                Delivery.create({
                    'backend_id': self.id,
                    'company_id': self.company_id.id,
                    'mapping_id': mapping.id,
                    'product_id': mapping.product_id.id,
                    'woo_product_id': woo_pid,
                    'lot_id': lot_data['lot'].id,
                    'lot_number': lot_number,
                    'quantity': lot_data['quantity'],
                    'expiration_month': lot_data['expiration_month'] or 0,
                    'expiration_year': lot_data['expiration_year'] or 0,
                    'delivery_hash': digest,
                    'state': 'published',
                    'response_message': (result or {}).get('message') if isinstance(result, dict) else False,
                })
                published += 1
        state = 'success' if not failed else ('partial' if published else 'error')
        log = self.env['amunet.woo.sync.log'].create({
            'backend_id': self.id,
            'company_id': self.company_id.id,
            'operation': 'stock_publish',
            'state': state,
            'date_end': fields.Datetime.now(),
            'total_count': published + skipped + failed,
            'done_count': published,
            'failed_count': failed,
            'message': '\n'.join(messages) or _(
                'Publicados %(pub)s lotes, %(skip)s ya estaban publicados.',
                pub=published, skip=skipped),
        })
        self.message_post(body=_(
            'Publicación de existencias APT -> tienda: %(pub)s nuevos, '
            '%(skip)s idempotentes, %(fail)s con error.',
            pub=published, skip=skipped, fail=failed))
        return log._action_open()

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Publicacion automatica (disparada por produccion / liberacion de lote)
    # ------------------------------------------------------------------

    @api.model
    def _auto_publish_product_lots(self, product, lot=None):
        """Publica (idempotente) los lotes LIBERADOS de un producto a la(s)
        tienda(s) con publicacion habilitada.

        Seguro por diseno: NUNCA lanza excepcion, para no bloquear el cierre
        de una orden de fabricacion ni la liberacion de un lote por Calidad.
        Solo actua si la tienda tiene ``allow_stock_publish`` (candado que en
        produccion permanece apagado hasta que Fernando lo habilite). Devuelve
        el numero de lotes publicados.
        """
        if not product:
            return 0
        published = 0
        backends = self.sudo().search([
            ("allow_stock_publish", "=", True),
            ("active", "=", True),
        ])
        for backend in backends:
            try:
                with self.env.cr.savepoint():
                    published += backend._publish_product_now(product, lot=lot)
            except Exception as exc:  # noqa: BLE001 - jamas debe propagar
                _logger.exception(
                    "Auto-publicacion a Woo fallo para %s en tienda %s: %s",
                    product.display_name, backend.name, exc)
        return published

    def _publish_product_now(self, product, lot=None):
        """Publica los lotes liberados de ``product`` para esta tienda.

        Reutiliza ``_read_released_piece_stock`` (solo lotes liberados con
        existencia libre en la ubicacion de piezas) y el ledger de idempotencia
        ``amunet.woo.stock.delivery``. Si se pasa ``lot`` solo publica ese lote.
        """
        self.ensure_one()
        if not self.allow_stock_publish:
            return 0
        if not self.apt_wp_user or not self.apt_wp_app_password:
            return 0
        Delivery = self.env["amunet.woo.stock.delivery"]
        mappings = self.env["amunet.woo.product.mapping"].search([
            ("backend_id", "=", self.id),
            ("relation_state", "=", "confirmed"),
            ("product_id", "=", product.id),
        ])
        published = 0
        for mapping in mappings:
            woo_pid = mapping.woo_product_id
            for lot_data in self._read_released_piece_stock(mapping):
                if lot and lot_data["lot"].id != lot.id:
                    continue
                lot_number = lot_data["lot_number"]
                if Delivery._already_published(self.id, woo_pid, lot_number):
                    continue
                payload = {
                    "product_id": woo_pid,
                    "quantity": lot_data["quantity"],
                    "expiration_month": lot_data["expiration_month"],
                    "expiration_year": lot_data["expiration_year"],
                    "lot_number": lot_number,
                    "notes": "Publicado automaticamente desde Odoo APT "
                             "(mapeo %s)" % mapping.id,
                }
                digest = Delivery._build_hash(self.id, woo_pid, lot_number)
                result = self._apt_deliver(payload)
                Delivery.create({
                    "backend_id": self.id,
                    "company_id": self.company_id.id,
                    "mapping_id": mapping.id,
                    "product_id": mapping.product_id.id,
                    "woo_product_id": woo_pid,
                    "lot_id": lot_data["lot"].id,
                    "lot_number": lot_number,
                    "quantity": lot_data["quantity"],
                    "expiration_month": lot_data["expiration_month"] or 0,
                    "expiration_year": lot_data["expiration_year"] or 0,
                    "delivery_hash": digest,
                    "state": "published",
                    "response_message": (result or {}).get("message")
                    if isinstance(result, dict) else False,
                })
                published += 1
        return published

    def action_test_connection(self):
        self.ensure_one()
        try:
            self._wc_get('products', params={'per_page': 1})
        except UserError as exc:
            self.write({'state': 'error', 'connection_message': str(exc)[:500]})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': _('WooCommerce'),
                    'message': str(exc),
                },
            }
        self.write({
            'state': 'connected',
            'connection_message': _('Conexión correcta (%s)') % fields.Datetime.now(),
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('WooCommerce'),
                'message': _('Conexión correcta con %s') % self.store_url,
            },
        }

    def action_import_catalog(self):
        """Lee el catálogo de Woo (solo GET) y crea/actualiza mapeos.

        El endpoint estándar de productos no conoce los estados operativos de
        APT (reservado/caducado/dañado), por lo que nunca crea snapshots.
        """
        self.ensure_one()
        Mapping = self.env['amunet.woo.product.mapping']
        created = updated = unmatched = 0
        messages = []
        page = 1
        try:
            while page <= WOO_MAX_PAGES:
                data, response = self._wc_get('products', params={
                    'per_page': WOO_BATCH_SIZE,
                    'page': page,
                    'status': 'any',
                })
                if not data:
                    break
                for woo_product in data:
                    # El tablero comercial solo admite productos Woo
                    # simples y padres variables. Tipos agregados por
                    # plugins ajenos (p. ej. el legado ATUM) no forman parte
                    # de este proceso y jamás se importan como pendientes.
                    if (woo_product.get('type') or '').lower() not in (
                            'simple', 'variable'):
                        continue
                    result = Mapping._upsert_from_woo(self, woo_product)
                    created += result in ('created', 'unmatched_created')
                    updated += result in ('updated', 'unmatched_updated')
                    if result.startswith('unmatched'):
                        unmatched += 1
                        messages.append(_(
                            'Pendiente sin producto Odoo para SKU "%(sku)s" '
                            '(%(name)s)',
                            sku=woo_product.get('sku') or '',
                            name=woo_product.get('name') or ''))
                total_pages = self._bounded_total_pages(response)
                if page >= total_pages:
                    break
                page += 1
        except UserError:
            # El error se muestra al usuario; la corrida fallida no deja
            # bitácora porque el rollback descartaría el registro.
            raise
        state = 'success' if not unmatched else 'partial'
        log = self.env['amunet.woo.sync.log'].create({
            'backend_id': self.id,
            'company_id': self.company_id.id,
            'operation': 'catalog_get',
            'state': state,
            'date_end': fields.Datetime.now(),
            'total_count': created + updated,
            'done_count': created + updated - unmatched,
            'failed_count': unmatched,
            'message': '\n'.join(messages) or _('Todos los SKU emparejados.'),
        })
        self.write({'last_read_date': fields.Datetime.now()})
        self.message_post(body=_(
            'Lectura GET del catálogo Woo: %(created)s mapeos nuevos, '
            '%(updated)s actualizados, %(unmatched)s SKU sin emparejar.',
            created=created, updated=updated, unmatched=unmatched))
        return log._action_open()

    def _fetch_variations(self, woo_product_id):
        variations = []
        page = 1
        while page <= WOO_MAX_PAGES:
            data, response = self._wc_get(
                'products/%s/variations' % woo_product_id,
                params={
                    'per_page': WOO_BATCH_SIZE,
                    'page': page,
                    'status': 'any',
                })
            variations.extend(data)
            total_pages = self._bounded_total_pages(response)
            if not data or page >= total_pages:
                break
            page += 1
        return variations

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
