# -*- coding: utf-8 -*-
"""Sincronización del manual del producto: Odoo (Nextcloud) → tienda.

El manual nace en `amunet.doc.compartida`, Calidad lo aprueba y firma, y el
módulo `amunet_manuales_nextcloud` lo sube a la carpeta de Nextcloud con el
nombre `CLAVE_Nombre.pdf`. De ahí sale la columna "Manual disponible".

Esto agrega el último tramo: bajar ese PDF y publicarlo en la tienda, siempre
en la MISMA URL canónica por clave
(`/wp-content/uploads/manuales/<CLAVE>.pdf`), de modo que la dirección del
manual no cambie nunca aunque cambie el archivo. El mu-plugin
`amunet-manual-odoo.php` de WordPress recibe el PDF por el puente firmado,
lo sobreescribe y hace que la ficha del producto —y las de sus gemelos de
caducidad corta y cortesía— apunten a esa URL.

La columna "Manual sincronizado" es la bitácora de la última corrida: se
enciende cuando el puente confirmó la publicación y se apaga si falló o si
el manual cambió en Nextcloud después.
"""

import base64
import hashlib
import json
import logging
from urllib.parse import quote

import requests
from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

NEXTCLOUD_TIMEOUT = 60

# Por que un manual no sale a la pagina
MOTIVO_NO_PUBLICA = [
    ('por_firmar', 'Version nueva esperando la firma de Calidad'),
    ('sin_firma', 'Manual nuevo o cambiado sin expediente firmado en Odoo'),
    ('sin_manual', 'Sin manual aprobado en Nextcloud'),
    ('ambiguo', 'Hay mas de un archivo para esta clave en la carpeta'),
]


class AmunetWooBackendManual(models.Model):
    _inherit = 'amunet.woo.backend'

    allow_manual_publish = fields.Boolean(
        string='Permitir publicar manuales en la tienda',
        default=False,
        help='Candado. Mientras esté apagado, Odoo no escribe ningún manual '
             'en la tienda aunque alguien pulse el botón.')


class AmunetWooSyncLogManual(models.Model):
    _inherit = 'amunet.woo.sync.log'

    operation = fields.Selection(
        selection_add=[('manual_publish', 'Publicación de manual en la tienda')],
        ondelete={'manual_publish': 'cascade'})


class AmunetWooProductMappingManual(models.Model):
    _inherit = 'amunet.woo.product.mapping'

    # ------------------------------------------------------------------
    # Estado de la publicación del manual en la tienda
    # ------------------------------------------------------------------
    # "Manual disponible" se calcula al vuelo contra la carpeta de Nextcloud,
    # así que sin esto no se podría filtrar por él en la pantalla.
    has_quality_manual = fields.Boolean(search='_search_has_quality_manual')

    def _search_has_quality_manual(self, operator, value):
        if operator not in ('=', '!=') or not isinstance(value, bool):
            raise UserError(_('Filtro no soportado para "Manual disponible".'))
        codes = list(self._manual_codes_map().keys())
        positivo = (operator == '=') == bool(value)
        if positivo:
            return [('product_id.default_code', 'in', codes)]
        return ['|', ('product_id', '=', False),
                ('product_id.default_code', 'not in', codes)]

    manual_sincronizado = fields.Boolean(
        string='Manual sincronizado', readonly=True, copy=False, index=True,
        help='El puente confirmó que la ficha de la tienda ya sirve este '
             'manual. Se apaga solo si el manual cambia en Nextcloud.')
    manual_sync_date = fields.Datetime(
        string='Sincronizado el', readonly=True, copy=False)
    manual_sync_url = fields.Char(
        string='Manual en la tienda', readonly=True, copy=False,
        help='URL canónica del PDF publicado. No cambia entre versiones.')
    manual_sync_sha = fields.Char(
        string='Huella del PDF', readonly=True, copy=False)
    manual_sync_archivo = fields.Char(
        string='Archivo publicado', readonly=True, copy=False)
    manual_sync_productos = fields.Char(
        string='Fichas actualizadas', readonly=True, copy=False,
        help='Claves de la tienda que quedaron apuntando a este manual '
             '(el producto y sus gemelos de caducidad corta / cortesía).')
    manual_origen = fields.Selection([
        ('firmado', 'Firmado en Odoo'),
        ('base', 'Base heredada'),
        ('por_firmar', 'Esperando firma'),
        ('sin_firma', 'Nuevo sin firma'),
        ('sin_manual', 'Sin manual'),
        ('ambiguo', 'Archivo duplicado'),
    ], string='Origen del manual', compute='_compute_manual_origen',
        help='Firmado = tiene expediente aprobado en Odoo. '
             'Base heredada = ya estaba antes de exigir firma. '
             'Esperando firma / Nuevo sin firma = NO se publica.')

    @api.depends('product_id')
    def _compute_manual_origen(self):
        for rec in self:
            rec.manual_origen = rec._manual_origen()[0]

    manual_sync_msg = fields.Char(
        string='Resultado', readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Descarga desde Nextcloud
    # ------------------------------------------------------------------
    def _manual_archivo_nextcloud(self):
        """Nombre del PDF del manual de este mapeo, según la carpeta Nextcloud."""
        self.ensure_one()
        codes = self._manual_codes_map()
        code = (self.product_id.default_code or '').strip().upper()
        return codes.get(code)

    # ------------------------------------------------------------------
    # Linea base de manuales (decision de Fernando, 10-sep-2026)
    # ------------------------------------------------------------------
    # Los manuales que ya estaban en la carpeta de Nextcloud cuando se congelo
    # la base son los "base": se publican tal cual, sin expediente de Calidad.
    # De ahi en adelante, TODO manual nuevo o modificado necesita expediente
    # aprobado y firmado en Odoo para poder publicarse.
    PARAM_BASE = 'amunet_woocommerce.manual_base_json'
    PARAM_BASE_FECHA = 'amunet_woocommerce.manual_base_fecha'

    def _manual_ambiguas_map(self):
        """Claves con mas de un archivo en la carpeta y sin forma de decidir."""
        raw = self.env['ir.config_parameter'].sudo().get_param(
            'amunet_woocommerce.manual_codes_ambiguas_json', '{}')
        try:
            return json.loads(raw) or {}
        except (ValueError, TypeError):
            return {}

    def _manual_base_map(self):
        """Dict {CLAVE: archivo.pdf} congelado como linea base."""
        raw = self.env['ir.config_parameter'].sudo().get_param(self.PARAM_BASE, '')
        if not raw:
            return None          # sin linea base fijada todavia
        try:
            return json.loads(raw) or {}
        except (ValueError, TypeError):
            return {}

    def action_congelar_linea_base(self):
        """Congela la carpeta actual como linea base. Se corre UNA vez."""
        ICP = self.env['ir.config_parameter'].sudo()
        if ICP.get_param(self.PARAM_BASE):
            raise UserError(_(
                'La linea base ya se congelo el %s. Volver a congelarla '
                'convertiria en "base" manuales que hoy exigen firma.')
                % ICP.get_param(self.PARAM_BASE_FECHA))
        codes = self._manual_codes_map()
        ICP.set_param(self.PARAM_BASE, json.dumps(codes))
        ICP.set_param(self.PARAM_BASE_FECHA,
                      fields.Datetime.to_string(fields.Datetime.now()))
        _logger.info('amunet_woocommerce: linea base de manuales congelada '
                     'con %d archivos', len(codes))
        return len(codes)

    def _manual_origen(self):
        """De donde sale el manual de esta clave y si se puede publicar.

        Devuelve (origen, publicable):
          'firmado'  -> hay expediente APROBADO y firmado en Odoo. Se publica.
          'base'     -> venia en la linea base congelada, tal cual. Se publica.
          'por_firmar' -> hay expediente pero NO aprobado. NO se publica.
          'sin_firma'  -> nuevo o cambiado respecto a la base y sin expediente
                          aprobado. NO se publica.
          'sin_manual' -> no hay archivo para esa clave.
        """
        self.ensure_one()
        fname = self._manual_archivo_nextcloud()
        if not fname:
            return ('sin_manual', False)

        # Dos archivos peleando por la misma clave: no adivinamos.
        clave_ = (self.product_id.default_code or '').strip().upper()
        if clave_ in self._manual_ambiguas_map():
            return ('ambiguo', False)

        docs = self.env['amunet.doc.compartida'].sudo().search(
            [('manual_filename', '=', fname)]) \
            if 'amunet.doc.compartida' in self.env \
            else self.env['amunet.woo.product.mapping']
        if docs:
            if any(d.state == 'aprobado' for d in docs):
                return ('firmado', True)
            return ('por_firmar', False)

        base = self._manual_base_map()
        if base is None:
            # Sin linea base congelada no hay con que comparar: no bloqueamos.
            return ('base', True)
        clave = (self.product_id.default_code or '').strip().upper()
        if base.get(clave) == fname:
            return ('base', True)
        return ('sin_firma', False)

    def _manual_aprobado_en_odoo(self):
        """True si este manual se puede publicar en la tienda."""
        self.ensure_one()
        return self._manual_origen()[1]

    def _manual_descargar(self, fname):
        """Baja el PDF de la carpeta compartida de Nextcloud."""
        url, token, _share = self._manual_config()
        destino = '%s%s' % (url, quote(fname))
        try:
            resp = requests.get(
                destino, auth=(token, ''), timeout=NEXTCLOUD_TIMEOUT)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise UserError(_(
                'No se pudo bajar el manual "%(f)s" de Nextcloud:\n%(e)s')
                % {'f': fname, 'e': exc})
        contenido = resp.content or b''
        if not contenido.startswith(b'%PDF'):
            raise UserError(_(
                'Lo que Nextcloud devolvió para "%s" no es un PDF. '
                'Revisa que el archivo siga en la carpeta de manuales.') % fname)
        return contenido

    # ------------------------------------------------------------------
    # Publicación hacia la tienda
    # ------------------------------------------------------------------
    def _manual_excluir_ids(self):
        """IDs Woo de los demás mapeos.

        Un producto que tiene mapeo propio nunca hereda el manual de un
        hermano: el puente lo salta aunque comparta raíz de inventario.
        """
        todos = self.search([])
        ids = set()
        for m in todos:
            if m.woo_product_id:
                ids.add(m.woo_product_id)
            if m.woo_parent_id:
                ids.add(m.woo_parent_id)
        return sorted(ids)

    def action_sincronizar_manual(self):
        """Publica en la tienda el manual aprobado de cada mapeo seleccionado."""
        registros = self or self.browse([])
        if not registros:
            return True
        backend = registros[0].backend_id
        if not backend.allow_manual_publish:
            raise UserError(_(
                'El candado de publicación de manuales está apagado en la '
                'tienda "%s". Enciéndelo antes de publicar.') % backend.name)

        excluir = registros._manual_excluir_ids()
        ok, fallo, detalle = 0, 0, []
        avisos = []
        inicio = fields.Datetime.now()

        for rec in registros:
            fname = rec._manual_archivo_nextcloud()
            if not fname:
                fallo += 1
                rec.write({
                    'manual_sincronizado': False,
                    'manual_sync_msg': _('Sin manual aprobado en Nextcloud'),
                })
                detalle.append('%s: sin manual en Nextcloud' % (rec.woo_sku or rec.id))
                continue
            if not rec._manual_aprobado_en_odoo():
                fallo += 1
                rec.write({
                    'manual_sincronizado': False,
                    'manual_sync_msg': dict(
                        MOTIVO_NO_PUBLICA).get(rec._manual_origen()[0],
                        _('Sin permiso para publicar')),
                })
                detalle.append('%s: %s' % (rec.woo_sku or rec.id,
                                           rec._manual_origen()[0]))
                continue
            destino_id = rec.woo_parent_id or rec.woo_product_id
            if not destino_id:
                fallo += 1
                rec.write({
                    'manual_sincronizado': False,
                    'manual_sync_msg': _('El mapeo no tiene producto en la tienda'),
                })
                detalle.append('%s: sin ID Woo' % (rec.woo_sku or rec.id))
                continue
            try:
                pdf = rec._manual_descargar(fname)
                respuesta = rec.backend_id._bridge_request(
                    'POST', 'product/%d/manual' % destino_id, payload={
                        'clave': (rec.product_id.default_code or rec.woo_sku or ''),
                        'filename': fname,
                        'pdf_base64': base64.b64encode(pdf).decode('ascii'),
                        'excluir_ids': excluir,
                    })
            except UserError as exc:
                fallo += 1
                rec.write({
                    'manual_sincronizado': False,
                    'manual_sync_msg': (str(exc) or '')[:250],
                })
                detalle.append('%s: %s' % (rec.woo_sku or rec.id, exc))
                continue

            productos = respuesta.get('productos') or []
            claves = ', '.join(
                str(p.get('sku') or p.get('id')) for p in productos)
            rec.write({
                'manual_sincronizado': True,
                'manual_sync_date': fields.Datetime.now(),
                'manual_sync_url': respuesta.get('url'),
                'manual_sync_sha': respuesta.get('sha256'),
                'manual_sync_archivo': fname,
                'manual_sync_productos': claves[:250],
                'manual_sync_msg': _('Publicado en %d ficha(s)') % len(productos),
            })
            ok += 1
            detalle.append('%s -> %s (%d fichas)' % (
                rec.woo_sku or rec.id, respuesta.get('url'), len(productos)))
            avisos.append(Markup(
                '<b>%s</b> &mdash; %s<br/>'
                'Archivo: %s<br/>'
                'Se descarga desde: <a href="%s">%s</a><br/>'
                'Fichas de producto actualizadas: %s'
            ) % (
                rec.product_id.default_code or rec.woo_sku or '',
                rec.woo_name or rec.product_name or '',
                fname,
                respuesta.get('url') or '',
                respuesta.get('url') or '',
                claves or str(len(productos)),
            ))
            _logger.info(
                'amunet_woocommerce: manual %s publicado en %s (%d fichas)',
                fname, respuesta.get('url'), len(productos))

        self.env['amunet.woo.sync.log'].sudo().create({
            'backend_id': backend.id,
            'company_id': backend.company_id.id,
            'operation': 'manual_publish',
            'state': 'success' if not fallo else ('partial' if ok else 'error'),
            'date_start': inicio,
            'date_end': fields.Datetime.now(),
            'total_count': len(registros),
            'done_count': ok,
            'failed_count': fallo,
            'message': '\n'.join(detalle)[:8000],
        })

        # Aviso por correo: el manual de la pagina acaba de cambiar.
        if avisos:
            if len(avisos) == 1:
                asunto = _('Manual actualizado en la pagina: %s') % (
                    registros[0].product_id.default_code
                    or registros[0].woo_sku or '')
            else:
                asunto = _('%d manuales actualizados en la pagina') % len(avisos)
            self.env['amunet.manual.aviso']._manual_aviso(
                asunto,
                _('El manual que se descarga desde la tienda ya es el de Odoo. '
                  'Esto es lo que se publico:'),
                avisos,
                pie=_('La direccion del manual no cambia nunca: siempre es la '
                      'misma URL por clave, asi que los enlaces que ya andan '
                      'por ahi siguen sirviendo.'))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Manuales publicados'),
                'message': _('%(ok)d publicados, %(ko)d con problema.')
                           % {'ok': ok, 'ko': fallo},
                'type': 'success' if not fallo else 'warning',
                'sticky': bool(fallo),
            },
        }

    # ------------------------------------------------------------------
    # Barrido diario: red de seguridad del enganche a la aprobacion
    # ------------------------------------------------------------------
    @api.model
    def _cron_publicar_manuales_pendientes(self):
        """Publica los manuales que quedaron pendientes.

        El disparo normal es la aprobacion del manual por Calidad. Este barrido
        recoge lo que se quedo atras porque la tienda no respondio, porque el
        candado estaba apagado ese dia, o porque el manual se cargo antes de que
        existiera el mapeo.
        """
        backend = self.env['amunet.woo.backend'].search(
            [('allow_manual_publish', '=', True)], limit=1)
        if not backend:
            return
        pendientes = self.search([
            ('backend_id', '=', backend.id),
            ('manual_sincronizado', '=', False),
            ('has_quality_manual', '=', True),
        ])
        for rec in pendientes:
            try:
                rec.action_sincronizar_manual()
                self.env.cr.commit()
            except Exception as exc:  # noqa: BLE001
                self.env.cr.rollback()
                _logger.warning(
                    'amunet_woocommerce: el barrido no pudo publicar el manual '
                    'de %s: %s', rec.woo_sku or rec.id, exc)

    # ------------------------------------------------------------------
    # Si el manual cambia en Nextcloud, "sincronizado" deja de ser cierto
    # ------------------------------------------------------------------
    def action_refresh_manuals(self):
        resultado = super().action_refresh_manuals()
        publicados = self.search([('manual_sincronizado', '=', True)])
        cambiados = []
        renombrados = 0
        for rec in publicados:
            fname = rec._manual_archivo_nextcloud()
            if fname and fname != rec.manual_sync_archivo:
                # El nombre cambio, pero eso no quiere decir que el manual sea
                # otro: Calidad renombra archivos (mayusculas, acentos, codigo
                # de instructivo) sin tocar el contenido. Si el PDF es el mismo,
                # la pagina sigue al dia: se anota el nombre nuevo y ya. Sin
                # esto, cada renombre desincronizaba el manual y mandaba un
                # aviso en falso.
                sha_nuevo = None
                try:
                    sha_nuevo = hashlib.sha256(
                        rec._manual_descargar(fname)).hexdigest()
                except Exception as exc:  # noqa: BLE001
                    _logger.warning(
                        'amunet_woocommerce: no se pudo comparar el contenido '
                        'de %s: %s', fname, exc)
                if sha_nuevo and rec.manual_sync_sha \
                        and sha_nuevo == rec.manual_sync_sha:
                    rec.write({'manual_sync_archivo': fname})
                    renombrados += 1
                    continue
                rec.write({
                    'manual_sincronizado': False,
                    'manual_sync_msg': _(
                        'El manual cambió en Nextcloud: falta volver a publicarlo'),
                })
                cambiados.append(Markup(
                    '<b>%s</b> &mdash; %s<br/>'
                    'Antes: %s<br/>'
                    'Ahora: %s'
                ) % (
                    rec.product_id.default_code or rec.woo_sku or '',
                    rec.woo_name or rec.product_name or '',
                    rec.manual_sync_archivo or '(sin registro)',
                    fname,
                ))

        if renombrados:
            _logger.info(
                'amunet_woocommerce: %d manual(es) solo cambiaron de nombre en '
                'Nextcloud; el contenido es el mismo y siguen publicados',
                renombrados)

        if cambiados:
            self.env['amunet.manual.aviso']._manual_aviso(
                _('Manual cambiado en Nextcloud: la pagina se quedo atras'),
                _('El archivo del manual cambio en Nextcloud, asi que la pagina '
                  'sigue mostrando la version anterior. Se publicara solo en '
                  'cuanto el manual tenga la firma de Calidad:'),
                cambiados)

        return resultado
