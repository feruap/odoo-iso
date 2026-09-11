# -*- coding: utf-8 -*-
"""Aviso por correo cuando cambia el manual de un producto.

Quien decide en la empresa no vive dentro de Odoo. Cuando Calidad sube una
version nueva de un manual, o cuando ese manual sale a la pagina, alguien
tiene que enterarse sin ir a revisar la pantalla. Este modelo manda ese correo.

A quien llega se controla desde Ajustes > Tecnico > Parametros del sistema, en
`amunet_woocommerce.manual_aviso_email`. Admite varias direcciones separadas
por coma. Para apagar los avisos hay que poner el valor `off`: borrar el
parametro no sirve, porque Odoo borra el registro y vuelve el valor por
defecto.

Regla de oro: un fallo al mandar el correo NUNCA tumba la aprobacion ni la
publicacion del manual. Se anota en el log y la operacion sigue.
"""

import logging

from markupsafe import Markup

from odoo import api, models

_logger = logging.getLogger(__name__)

PARAM_EMAIL = 'amunet_woocommerce.manual_aviso_email'
EMAIL_POR_DEFECTO = 'gestion@amunet.com.mx'


class AmunetManualAviso(models.AbstractModel):
    _name = 'amunet.manual.aviso'
    _description = 'Aviso por correo de cambios de manual'

    @api.model
    def _manual_aviso_destinatarios(self):
        """Direcciones a las que va el aviso, como cadena lista para email_to."""
        crudo = self.env['ir.config_parameter'].sudo().get_param(
            PARAM_EMAIL, EMAIL_POR_DEFECTO) or ''
        if crudo.strip().lower() in ('off', 'no', 'ninguno', '-'):
            return ''
        correos = [c.strip() for c in crudo.replace(';', ',').split(',')
                   if c.strip() and '@' in c]
        return ', '.join(correos)

    @api.model
    def _manual_aviso(self, asunto, encabezado, lineas, pie=''):
        """Manda un correo de aviso. Devuelve True si se creo el mensaje."""
        destino = self._manual_aviso_destinatarios()
        if not destino or not lineas:
            return False

        ICP = self.env['ir.config_parameter'].sudo()
        base_url = (ICP.get_param('web.base.url') or '').rstrip('/')

        partes = [Markup('<p>%s</p>') % encabezado, Markup('<ul>')]
        for linea in lineas:
            partes.append(Markup('<li>%s</li>') % linea)
        partes.append(Markup('</ul>'))
        if pie:
            partes.append(Markup('<p>%s</p>') % pie)
        if base_url:
            partes.append(Markup(
                '<p>Mapeo de productos y manuales: '
                '<a href="%s/odoo/action-1109">%s/odoo/action-1109</a></p>'
            ) % (base_url, base_url))
        partes.append(Markup(
            '<p style="color:#888888;font-size:12px">Aviso automatico del modulo '
            'de manuales de Odoo. Para cambiar a quien llega, edita el parametro '
            'del sistema <code>%s</code>.</p>') % PARAM_EMAIL)

        try:
            correo = self.env['mail.mail'].sudo().create({
                'subject': asunto,
                'email_to': destino,
                'body_html': Markup('').join(partes),
                'auto_delete': False,
            })
            correo.send(raise_exception=False)
            if correo.exists() and correo.state == 'exception':
                _logger.warning(
                    'amunet_woocommerce: el aviso de manual "%s" para %s quedo '
                    'en excepcion: %s. Revisa el servidor de correo saliente.',
                    asunto, destino, correo.failure_reason or 'sin detalle')
                return False
            _logger.info(
                'amunet_woocommerce: aviso de manual enviado a %s (%s)',
                destino, asunto)
            return True
        except Exception as exc:  # noqa: BLE001
            _logger.warning(
                'amunet_woocommerce: no se pudo mandar el aviso de manual "%s" '
                'a %s: %s', asunto, destino, exc)
            return False