# -*- coding: utf-8 -*-
import base64
import logging
from urllib.parse import quote

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AmunetDocumentoNextcloud(models.Model):
    _inherit = 'amunet.documento'

    url_nextcloud = fields.Char(
        string='Enlace Nextcloud',
        readonly=True,
        help='URL del PDF en Nextcloud. Se llena automaticamente al aprobar el manual.',
    )

    def write(self, vals):
        candidatos = []
        if vals.get('state') == 'vigente':
            candidatos = self.filtered(
                lambda r: r.tipo == 'manual' and r.state != 'vigente'
            ).ids

        result = super().write(vals)

        if candidatos:
            for rec in self.browse(candidatos).exists():
                filename = rec.archivo_filename or ''
                if rec.archivo and filename and '_' in filename:
                    rec._subir_a_nextcloud()
                else:
                    motivos = []
                    if not rec.archivo:
                        motivos.append('sin archivo PDF adjunto')
                    if not filename:
                        motivos.append('sin nombre de archivo')
                    elif '_' not in filename:
                        motivos.append(
                            'el nombre "%s" no tiene el formato CODIGO_NOMBRE.pdf' % filename
                        )
                    rec.message_post(
                        body=(
                            '<p><b>Nextcloud:</b> Manual aprobado pero no se subio '
                            'automaticamente: %s.</p>'
                        ) % ', '.join(motivos)
                    )

        return result

    def _subir_a_nextcloud(self):
        """Sube self.archivo a Nextcloud, luego limpia el binario de Odoo."""
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
                    body='<p><b>Nextcloud:</b> Faltan parametros del sistema '
                         '(nextcloud.manuales.url, .user o .password). '
                         'Pide a desarrollo que los configure.</p>'
                )
                return

            content = base64.b64decode(self.archivo)
            filename = self.archivo_filename
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
                self._limpiar_binario_y_guardar_url(file_url)
                self.message_post(
                    body='<p><b>Nextcloud [OK]:</b> Manual subido y PDF liberado de Odoo. '
                         '<a href="%s" target="_blank">Ver manual en Nextcloud</a>.</p>'
                         % file_url
                )
                _logger.info(
                    'amunet_manuales_nextcloud: subido %s → HTTP %s; binario liberado',
                    filename, resp.status_code,
                )
                # Propuesta 1: refrescar al instante la columna "Tiene manual" del
                # tablero Woo (sin esperar el cron diario). Guardado por si el
                # modulo amunet_woocommerce no esta instalado o el refresco falla.
                if 'amunet.woo.product.mapping' in self.env:
                    try:
                        self.env['amunet.woo.product.mapping'].sudo().action_refresh_manuals()
                    except Exception:
                        _logger.warning(
                            'amunet_manuales_nextcloud: no se pudo refrescar '
                            '"Tiene manual" del tablero Woo tras subir %s', filename)
            else:
                self.message_post(
                    body=(
                        '<p><b>Nextcloud [Error]:</b> No se pudo subir <b>%s</b>. '
                        'Servidor respondio HTTP %s. Contacta a desarrollo.</p>'
                    ) % (filename, resp.status_code)
                )
                _logger.error(
                    'amunet_manuales_nextcloud: error HTTP %s subiendo %s',
                    resp.status_code, filename,
                )

        except Exception as exc:
            _logger.exception(
                'amunet_manuales_nextcloud: excepcion al subir %s', self.archivo_filename
            )
            self.message_post(
                body='<p><b>Nextcloud [Error]:</b> Excepcion: %s. Contacta a desarrollo.</p>'
                     % str(exc)
            )

    def _limpiar_binario_y_guardar_url(self, url):
        """Elimina el PDF de Odoo y guarda el enlace a Nextcloud."""
        self.ensure_one()
        # Eliminar el attachment binario directamente (evita el bloqueo ORM de campos vigentes)
        self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'amunet.documento'),
            ('res_id', '=', self.id),
            ('res_field', '=', 'archivo'),
        ]).unlink()
        # Limpiar filename y guardar URL via SQL para no pasar por las restricciones ORM
        self.env.cr.execute(
            "UPDATE amunet_documento SET archivo_filename = NULL, "
            "url_nextcloud = %s, write_date = NOW() WHERE id = %s",
            [url, self.id],
        )
        self.invalidate_recordset(['archivo', 'archivo_filename', 'url_nextcloud'])
