# -*- coding: utf-8 -*-
import base64
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AmunetDocumentoNextcloud(models.Model):
    _inherit = 'amunet.documento'

    def write(self, vals):
        # Captura los manuales que van a pasar a vigente antes de super()
        candidatos = []
        if vals.get('state') == 'vigente':
            candidatos = self.filtered(
                lambda r: r.tipo == 'manual' and r.state != 'vigente'
            ).ids

        result = super().write(vals)

        # Despues de que el estado quedo guardado, sube a Nextcloud
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
        """Sube self.archivo a la carpeta de Nextcloud configurada en parametros del sistema."""
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

            if not nc_url or not nc_user or not nc_pass:
                msg = (
                    '<p><b>Nextcloud:</b> Faltan parametros del sistema '
                    '(nextcloud.manuales.url, .user o .password). '
                    'Pide a desarrollo que los configure en Ajustes > Parametros del sistema.</p>'
                )
                _logger.warning(
                    'amunet_manuales_nextcloud: parametros incompletos; no se subiò %s',
                    self.archivo_filename,
                )
                self.message_post(body=msg)
                return

            content = base64.b64decode(self.archivo)
            filename = self.archivo_filename
            url = '{}/remote.php/dav/files/{}/{}/{}'.format(
                nc_url, nc_user, nc_folder, filename
            )

            resp = requests.put(
                url,
                data=content,
                auth=HTTPBasicAuth(nc_user, nc_pass),
                timeout=30,
            )

            if resp.status_code in (200, 201, 204):
                self.message_post(
                    body='<p><b>Nextcloud [OK]:</b> Manual subido correctamente: <b>%s</b>.</p>'
                         % filename
                )
                _logger.info(
                    'amunet_manuales_nextcloud: subido %s → HTTP %s',
                    filename, resp.status_code,
                )
            else:
                self.message_post(
                    body=(
                        '<p><b>Nextcloud [Error]:</b> No se pudo subir <b>%s</b>. '
                        'El servidor respondio HTTP %s. Contacta a desarrollo.</p>'
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
                body='<p><b>Nextcloud [Error]:</b> Excepcion al subir el manual: %s. '
                     'Contacta a desarrollo.</p>' % str(exc)
            )
