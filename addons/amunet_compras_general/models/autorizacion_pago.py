# -*- coding: utf-8 -*-
"""Autorizacion de pago de una compra general.

Odoo NO habla con Telegram. Cuando el jefe autoriza una solicitud de
compra general, aqui solo se deja la marca `por_enviar` y se genera un
token firmado. Un servicio aparte (amunet-pagos-bot) recoge las marcadas,
manda el mensaje a Fernando y vuelve a escribir el resultado.

Se separa a proposito: una llamada HTTP dentro de la transaccion de Odoo
deja al usuario esperando y, si Telegram tarda o falla, tumba la
aprobacion entera. Asi, si el bot esta caido, la aprobacion se guarda y
el mensaje sale cuando el bot vuelve.
"""

import hashlib
import hmac
import secrets

from odoo import _, api, fields, models

PARAM_SECRETO = 'amunet_compras_general.hmac_secret'


class AmunetMaterialRequest(models.Model):
    _inherit = 'amunet.material.request'

    amunet_concepto_pago = fields.Char(string='Concepto de pago', tracking=True)

    amunet_autorizacion_estado = fields.Selection(
        selection=[
            ('na', 'No aplica'),
            ('por_enviar', 'Por avisar a Fernando'),
            ('pendiente', 'Esperando a Fernando'),
            ('autorizado', 'Autorizado'),
            ('rechazado', 'Rechazado'),
        ],
        string='Autorizacion de pago',
        default='na',
        copy=False,
        tracking=True,
    )
    amunet_autorizacion_token = fields.Char(copy=False, groups='base.group_system')
    amunet_autorizacion_fecha = fields.Datetime(string='Fecha de autorizacion', copy=False, readonly=True)
    amunet_telegram_msg_id = fields.Char(copy=False, groups='base.group_system')

    @api.model
    def _amunet_hmac_secret(self):
        ICP = self.env['ir.config_parameter'].sudo()
        secreto = ICP.get_param(PARAM_SECRETO)
        if not secreto:
            secreto = secrets.token_hex(32)
            ICP.set_param(PARAM_SECRETO, secreto)
        return secreto

    def _amunet_firma(self, respuesta):
        """Firma corta para el callback_data de Telegram (limite 64 bytes)."""
        self.ensure_one()
        mensaje = '%s|%s|%s' % (self.id, self.amunet_autorizacion_token or '', respuesta)
        return hmac.new(
            self._amunet_hmac_secret().encode(),
            mensaje.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]

    def action_head_approve(self):
        resultado = super().action_head_approve()
        for req in self:
            if req.request_type != 'general' or not req.amunet_forma_pago:
                continue
            if req.amunet_autorizacion_estado not in ('na', False):
                continue
            req.sudo().write({
                'amunet_autorizacion_estado': 'por_enviar',
                'amunet_autorizacion_token': secrets.token_urlsafe(9),
            })
            req.message_post(body=_(
                'Autorizada por el jefe. Se le pedira el visto bueno a Fernando por Telegram '
                'antes de comprar o de pedir la transferencia.'
            ))
        return resultado
