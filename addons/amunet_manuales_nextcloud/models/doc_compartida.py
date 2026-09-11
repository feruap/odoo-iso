# -*- coding: utf-8 -*-
import base64
import logging
from urllib.parse import quote

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DocCompartidaNextcloud(models.Model):
    _inherit = 'amunet.doc.compartida'

    url_nextcloud = fields.Char(
        string='Enlace Nextcloud',
        readonly=True,
        help='URL del PDF en Nextcloud. Se llena automaticamente al aprobar el manual.',
    )
    producto_id = fields.Many2one(
        'product.product',
        string='Producto del manual',
        domain="[('default_code', '!=', False)]",
        help='De aqui sale la clave con la que tiene que empezar el archivo. '
             'Al elegirlo, el nombre del PDF se corrige solo.',
    )
    manual_sin_producto = fields.Boolean(
        string='No es manual de producto',
        help='Marcalo para manuales que no van a la tienda: equipos, balanzas, '
             'procedimientos internos. Con esto el sistema deja de exigir la '
             'clave del producto en el nombre del archivo.',
    )
    manual_clave = fields.Char(
        string='Clave del archivo',
        compute='_compute_manual_clave',
        help='Lo que el sistema lee antes del primer "_" del nombre del archivo.',
    )
    manual_nombre_ok = fields.Boolean(
        string='Nombre correcto',
        compute='_compute_manual_clave',
        help='El archivo empieza con una clave de producto que existe en Odoo. '
             'Si esta apagado, el manual NO puede subir a Nextcloud ni llegar '
             'a la pagina, aunque se apruebe.',
    )

    enlace_pdf = fields.Html(
        string='PDF',
        compute='_compute_enlace_pdf',
        sanitize=False,
        store=False,
    )

    @api.depends('url_nextcloud', 'manual_filename', 'manual_file')
    def _compute_enlace_pdf(self):
        for rec in self:
            if not rec.manual_filename:
                rec.enlace_pdf = False
                continue
            if rec.url_nextcloud:
                url = rec.url_nextcloud
            elif rec.manual_file and isinstance(rec.id, int):
                url = (
                    '/web/content?model=amunet.doc.compartida'
                    '&id=%d&field=manual_file&filename=%s&download=true'
                ) % (rec.id, rec.manual_filename)
            else:
                rec.enlace_pdf = False
                continue
            rec.enlace_pdf = (
                '<a href="%s" target="_blank" style="white-space:nowrap">'
                '<i class="fa fa-download" style="margin-right:5px"></i>%s</a>'
            ) % (url, rec.manual_filename)

    @api.depends('manual_filename')
    def _compute_manual_clave(self):
        Prod = self.env['product.product'].with_context(active_test=False).sudo()
        for rec in self:
            base = (rec.manual_filename or '').rsplit('.', 1)[0]
            clave = base.split('_')[0].strip().upper() if '_' in base else ''
            rec.manual_clave = clave
            rec.manual_nombre_ok = bool(clave) and bool(
                Prod.search_count([('default_code', '=ilike', clave)]))

    @staticmethod
    def _nombre_con_clave(filename, clave):
        """Devuelve el nombre con CLAVE_ al principio, sin duplicarla."""
        filename = (filename or '').strip()
        clave = (clave or '').strip()
        if not filename or not clave:
            return filename
        if filename.upper().startswith(clave.upper() + '_'):
            return filename
        return '%s_%s' % (clave, filename)

    @api.onchange('producto_id')
    def _onchange_producto_id(self):
        """Al elegir el producto, el archivo se renombra a CLAVE_Nombre.pdf."""
        for rec in self:
            if rec.producto_id and rec.manual_filename:
                rec.manual_filename = rec._nombre_con_clave(
                    rec.manual_filename, rec.producto_id.default_code)

    def _check_nombre_manual(self):
        """El nombre tiene que empezar con la clave del producto.

        Sin eso el manual se aprueba y firma pero NO sube a Nextcloud ni llega
        a la pagina: el sistema no sabe a que producto pertenece. Paso en
        13 manuales aprobados (Tuberculosis.pdf, CHAGAS.pdf, TFB_..., etc.)
        que quedaron firmados y nunca se publicaron.
        """
        self.ensure_one()
        if self.manual_sin_producto:
            return
        if not self.manual_file or self.manual_nombre_ok:
            return
        raise UserError(
            'El archivo se llama "%s" y no empieza con la clave del producto.\n\n'
            'Asi el sistema no sabe a que producto pertenece: el manual se '
            'aprobaria y firmaria, pero NO subiria a Nextcloud ni llegaria a la '
            'pagina.\n\n'
            'Como se arregla, lo mas facil: elige el producto en el campo '
            '"Producto del manual" y el nombre se corrige solo.\n'
            'A mano: ponle el formato CLAVE_Nombre.pdf, por ejemplo '
            '"DMATB01_Tuberculosis.pdf".\n\n'
            'Las claves se ven en Mapeos y consulta de productos (accion 1109).\n\n'
            'Si este manual NO es de un producto (un equipo, una balanza, un '
            'procedimiento interno), marca la casilla "No es manual de '
            'producto" y podras aprobarlo tal cual.'
            % (self.manual_filename or '(sin archivo)'))

    def write(self, vals):
        if vals.get('state') == 'aprobado':
            for rec in self:
                if rec.state != 'aprobado':
                    rec._check_nombre_manual()

        candidatos_aprobar = []
        candidatos_reemplazar = []

        if vals.get('state') == 'aprobado':
            candidatos_aprobar = self.filtered(lambda r: r.state != 'aprobado').ids

        if vals.get('manual_file') and not vals.get('state'):
            candidatos_reemplazar = self.filtered(lambda r: r.url_nextcloud).ids

        result = super().write(vals)

        for rec in self.browse(candidatos_aprobar).exists():
            filename = rec.manual_filename or ''
            if rec.manual_file and filename and '_' in filename:
                rec._subir_manual_a_nextcloud(es_reemplazo=False)
            else:
                motivos = []
                if not rec.manual_file:
                    motivos.append('sin archivo PDF adjunto')
                if not filename or '_' not in filename:
                    motivos.append(
                        'el nombre "%s" no tiene el formato CODIGO_NOMBRE.pdf' % filename
                    )
                rec.message_post(
                    body='<p><b>Nextcloud:</b> Manual no subido automaticamente: %s.</p>'
                         % ', '.join(motivos)
                )

        for rec in self.browse(candidatos_reemplazar).exists():
            filename = rec.manual_filename or ''
            if rec.manual_file and filename and '_' in filename:
                rec._subir_manual_a_nextcloud(es_reemplazo=True)
            else:
                motivos = []
                if not rec.manual_file:
                    motivos.append('sin archivo PDF adjunto')
                if not filename or '_' not in filename:
                    motivos.append(
                        'el nombre "%s" no tiene el formato CODIGO_NOMBRE.pdf' % filename
                    )
                rec.message_post(
                    body='<p><b>Nextcloud:</b> Reemplazo no procesado: %s.</p>'
                         % ', '.join(motivos)
                )

        return result

    def _subir_manual_a_nextcloud(self, es_reemplazo=False):
        """Sube manual_file a Nextcloud y limpia el binario de Odoo."""
        self.ensure_one()
        try:
            import requests
            from requests.auth import HTTPBasicAuth

            ICP = self.env['ir.config_parameter'].sudo()
            nc_url    = (ICP.get_param('nextcloud.manuales.url') or '').rstrip('/')
            nc_user   = ICP.get_param('nextcloud.manuales.user') or ''
            nc_pass   = ICP.get_param('nextcloud.manuales.password') or ''
            nc_folder = (
                ICP.get_param('nextcloud.manuales.folder') or 'Drive-Migration/Manuales'
            ).strip('/')
            share_url = (ICP.get_param('nextcloud.manuales.share_url') or '').rstrip('/')

            if not nc_url or not nc_user or not nc_pass:
                self.message_post(
                    body='<p><b>Nextcloud:</b> Faltan parametros del sistema. '
                         'Pide a desarrollo que los configure.</p>'
                )
                return

            content = base64.b64decode(self.manual_file)
            filename = self.manual_filename
            upload_url = '{}/remote.php/dav/files/{}/{}/{}'.format(
                nc_url, nc_user, nc_folder, filename
            )

            resp = requests.put(
                upload_url,
                data=content,
                auth=HTTPBasicAuth(nc_user, nc_pass),
                timeout=30,
            )

            if resp.status_code in (200, 201, 204):
                file_url = (
                    '{}/download?path=%2F&files={}'.format(share_url, quote(filename))
                    if share_url else upload_url
                )
                self._limpiar_manual_binario(file_url)
                if es_reemplazo:
                    self._resetear_a_por_aprobar()
                    # La tienda sigue con la version anterior: que la 1109 lo diga.
                    self._marcar_tienda_desactualizada(filename)
                self.message_post(
                    body='<p><b>Nextcloud [OK]:</b> Manual subido y PDF liberado de Odoo. '
                         '<a href="%s" target="_blank">Ver manual en Nextcloud</a>.</p>'
                         % file_url
                )
                _logger.info(
                    'amunet_manuales_nextcloud: subido %s → HTTP %s; binario liberado',
                    filename, resp.status_code,
                )
                # Refrescar al instante "Manual disponible" del tablero Woo.
                if 'amunet.woo.product.mapping' in self.env:
                    try:
                        self.env['amunet.woo.product.mapping'].sudo().action_refresh_manuals()
                    except Exception:
                        _logger.warning(
                            'amunet_manuales_nextcloud: no se pudo refrescar '
                            '"Manual disponible" del tablero Woo tras subir %s', filename)
                    # Y publicarlo en la tienda. Solo al APROBAR: en un reemplazo el
                    # PDF nuevo regresa a "listo para aprobar" y no debe salir aun.
                    if not es_reemplazo:
                        self._publicar_manual_en_tienda(filename)
            else:
                self.message_post(
                    body='<p><b>Nextcloud [Error]:</b> No se pudo subir <b>%s</b>. '
                         'HTTP %s. Contacta a desarrollo.</p>' % (filename, resp.status_code)
                )

        except Exception as exc:
            _logger.exception(
                'amunet_manuales_nextcloud: excepcion al subir %s', self.manual_filename
            )
            self.message_post(
                body='<p><b>Nextcloud [Error]:</b> %s. Contacta a desarrollo.</p>' % str(exc)
            )

    def _publicar_manual_en_tienda(self, filename):
        """Publica en WooCommerce el manual recien aprobado.

        Se llama sola al aprobar. Nunca tumba la aprobacion: si la tienda no
        responde o el candado esta apagado, lo deja anotado en la conversacion
        del manual y el barrido diario lo reintenta.
        """
        self.ensure_one()
        base = (filename or '').rsplit('.', 1)[0]
        clave = base.split('_')[0].strip().upper()
        if not clave:
            return
        Mapeo = self.env['amunet.woo.product.mapping'].sudo()
        mapeos = Mapeo.search([('default_code', '=', clave)])
        if not mapeos:
            if 'amunet.manual.aviso' in self.env:
                self.env['amunet.manual.aviso']._manual_aviso(
                    'Manual aprobado sin producto mapeado: %s' % clave,
                    'Se aprobo este manual pero no hay ningun producto de la '
                    'tienda mapeado a su clave, asi que NO se publico:',
                    [Markup('<b>%s</b><br/>Archivo: %s') % (clave, filename or '')],
                    pie='Hay que darlo de alta en el mapeo para que llegue a la '
                        'pagina.')
            self.message_post(
                body=Markup('<p><b>Tienda:</b> no hay ning\u00fan producto de la tienda '
                     'mapeado a la clave <b>%s</b>, as\u00ed que el manual no se '
                     'public\u00f3. Rev\u00edsalo en Mapeos y consulta de productos.</p>'
                     % clave),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
            return
        try:
            mapeos.action_sincronizar_manual()
        except Exception as exc:  # noqa: BLE001
            _logger.warning(
                'amunet_manuales_nextcloud: no se pudo publicar %s en la tienda: %s',
                filename, exc)
            self.message_post(
                body=Markup('<p><b>Tienda [pendiente]:</b> el manual no se pudo publicar '
                            'todav\u00eda (%s). El barrido diario lo reintenta; tambi\u00e9n se '
                            'puede correr a mano desde Mapeos y consulta de productos.</p>')
                     % str(exc)[:200],
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
            return
        publicados = mapeos.filtered(lambda m: m.manual_sincronizado)
        if publicados:
            self.message_post(
                body=Markup('<p><b>Tienda [OK]:</b> el manual ya se descarga desde la p\u00e1gina: '
                     '<a href="%s" target="_blank">%s</a> (%d ficha(s) de producto).</p>'
                     % (publicados[0].manual_sync_url, publicados[0].manual_sync_url,
                        len(publicados))),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
        else:
            self.message_post(
                body=Markup('<p><b>Tienda [pendiente]:</b> la publicaci\u00f3n no qued\u00f3: %s</p>')
                     % (mapeos[0].manual_sync_msg or 'sin detalle'),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

    def _marcar_tienda_desactualizada(self, filename):
        """Al subir una version nueva del PDF, la tienda deja de estar al dia.

        El manual regresa a "listo para aprobar" y NO se publica hasta que
        Calidad lo apruebe, asi que "Manual sincronizado" tiene que apagarse.
        Sin esto la columna se quedaba en verde con el PDF viejo en la pagina,
        porque solo comparaba el NOMBRE del archivo y en un reemplazo el nombre
        casi siempre es el mismo.
        """
        self.ensure_one()
        if 'amunet.woo.product.mapping' not in self.env:
            return
        base = (filename or '').rsplit('.', 1)[0]
        clave = base.split('_')[0].strip().upper()
        if not clave:
            return
        mapeos = self.env['amunet.woo.product.mapping'].sudo().search([
            ('default_code', '=', clave),
            ('manual_sincronizado', '=', True),
        ])
        if not mapeos:
            return
        mapeos.write({
            'manual_sincronizado': False,
            'manual_sync_msg': 'Version nueva esperando aprobacion de Calidad',
        })
        if 'amunet.manual.aviso' in self.env:
            lineas = [
                Markup('<b>%s</b> &mdash; %s<br/>Archivo nuevo: %s')
                % (m.product_id.default_code or m.woo_sku or clave,
                   m.woo_name or m.product_name or '', filename or '')
                for m in mapeos
            ]
            self.env['amunet.manual.aviso']._manual_aviso(
                'Manual reemplazado, esperando firma de Calidad: %s' % clave,
                'Se subio una version nueva de este manual. Mientras Calidad no '
                'la apruebe, la pagina sigue mostrando la version anterior:',
                lineas,
                pie='En cuanto se apruebe, se publica sola en la tienda.')
        self.message_post(
            body=Markup('<p><b>Tienda:</b> la p\u00e1gina sigue mostrando la versi\u00f3n '
                        'anterior. Se publicar\u00e1 sola en cuanto Calidad apruebe esta '
                        'versi\u00f3n (%d producto(s) en espera).</p>') % len(mapeos),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

    def _resetear_a_por_aprobar(self):
        """Regresa el manual a 'por_aprobar' cuando se sube una nueva versión del PDF."""
        self.ensure_one()
        self.env.cr.execute(
            "UPDATE amunet_doc_compartida SET state = 'por_aprobar', write_date = NOW() WHERE id = %s",
            [self.id],
        )
        self.invalidate_recordset(['state'])
        calidad = self._usuarios_calidad()
        self.message_post(
            body='<p>Se subió una nueva versión del PDF a Nextcloud. '
                 'El manual queda <b>listo para aprobar</b>; Calidad debe revisar la nueva versión.</p>',
            message_type='notification',
            subtype_xmlid='mail.mt_note',
            partner_ids=calidad.mapped('partner_id').ids,
        )

    @api.model
    def _cron_recordatorio_calidad(self):
        """Cada 2 horas: notifica en Odoo a Calidad sobre manuales pendientes de aprobación."""
        pendientes = self.search([('state', '=', 'por_aprobar')])
        if not pendientes:
            return
        ahora = fields.Datetime.now()
        for rec in pendientes:
            delta = ahora - (rec.write_date or ahora)
            horas = int(delta.total_seconds() // 3600)
            mins = int((delta.total_seconds() % 3600) // 60)
            tiempo = '%dh %dmin' % (horas, mins) if horas else '%d min' % mins
            calidad = rec._usuarios_calidad() - rec._usuarios_validacion()
            if not calidad:
                continue
            rec.message_post(
                body='<p>⏰ <b>Recordatorio:</b> Este manual lleva <b>%s</b> '
                     'esperando aprobación de Calidad.</p>' % tiempo,
                message_type='notification',
                subtype_xmlid='mail.mt_note',
                partner_ids=calidad.mapped('partner_id').ids,
            )

    def _limpiar_manual_binario(self, url):
        """Elimina el binario PDF de Odoo y guarda el enlace a Nextcloud.
        Conserva manual_filename para que el link siga mostrando el nombre del archivo."""
        self.ensure_one()
        self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'amunet.doc.compartida'),
            ('res_id', '=', self.id),
            ('res_field', '=', 'manual_file'),
        ]).unlink()
        self.env.cr.execute(
            "UPDATE amunet_doc_compartida SET url_nextcloud = %s, write_date = NOW() WHERE id = %s",
            [url, self.id],
        )
        self.invalidate_recordset(['manual_file', 'url_nextcloud', 'enlace_pdf'])
