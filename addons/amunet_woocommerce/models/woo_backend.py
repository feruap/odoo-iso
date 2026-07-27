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
    # Acciones
    # ------------------------------------------------------------------

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
                    # La relación comercial es siempre el producto simple o
                    # el padre variable. Las variaciones son presentaciones,
                    # no productos Odoo independientes.
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
