# -*- coding: utf-8 -*-
<<<<<<< HEAD
"""Autorizacion de pago de una solicitud de compra.

Odoo NO habla con Telegram. Cuando el jefe autoriza una solicitud de
compra, aqui solo se deja la marca `por_enviar` y se genera un token
firmado. Un servicio aparte (amunet-pagos-bot) recoge las marcadas,
=======
"""Autorizacion de pago de una compra general.

Odoo NO habla con Telegram. Cuando el jefe autoriza una solicitud de
compra general, aqui solo se deja la marca `por_enviar` y se genera un
token firmado. Un servicio aparte (amunet-pagos-bot) recoge las marcadas,
>>>>>>> origin/main
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
from odoo.exceptions import UserError

PARAM_SECRETO = 'amunet_compras_general.hmac_secret'


<<<<<<< HEAD
class AmunetSolicitudCompra(models.Model):
    _inherit = 'amunet.solicitud.compra'
=======
class AmunetMaterialRequest(models.Model):
    _inherit = 'amunet.material.request'
>>>>>>> origin/main

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
<<<<<<< HEAD
    amunet_autorizacion_fecha = fields.Datetime(string='Fecha de autorizacion de pago', copy=False, readonly=True)
=======
    amunet_autorizacion_fecha = fields.Datetime(string='Fecha de autorizacion', copy=False, readonly=True)
>>>>>>> origin/main
    amunet_telegram_msg_id = fields.Char(copy=False, groups='base.group_system')

    # -- corte de pagos y comprobante -------------------------------------
    # Las ordenes de pago autorizadas NO salen al grupo de una en una: se
    # acumulan y salen juntas en el corte de las 15:00 de lunes a viernes.
    # Quien paga responde a esa orden con la foto del comprobante, y ahi se
    # cierra el circulo.
    amunet_pago_publicado = fields.Datetime(
        string='Publicado al grupo de pagos', copy=False, readonly=True)
    amunet_telegram_grupo_msg_id = fields.Char(copy=False, groups='base.group_system')
    amunet_comprobante_fecha = fields.Datetime(
        string='Comprobante recibido', copy=False, readonly=True)
    amunet_comprobante_archivo = fields.Char(
        string='Archivo del comprobante', copy=False, readonly=True,
        groups='amunet_compras_general.group_compras_monto')

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

    def _amunet_encolar_autorizacion(self):
        """Deja la solicitud lista para que el bot le pida el visto bueno a
        Fernando. Se separa del boton para que sirva a los dos caminos."""
        for req in self:
            if req.amunet_autorizacion_estado not in ('na', False):
                continue
            req.sudo().write({
                'amunet_autorizacion_estado': 'por_enviar',
                'amunet_autorizacion_token': secrets.token_urlsafe(9),
            })
            req.message_post(body=_(
                'Se le pedira el visto bueno a Fernando por Telegram antes de '
                'comprar o de pedir la transferencia.'))

    def action_pedir_autorizacion_pago(self):
        """Camino para las solicitudes cuyo solicitante NO tiene jefe asignado.

<<<<<<< HEAD
        El disparo normal vive en action_autorizar, pero parte de la gente no
        tiene jefe en Recursos Humanos: esas solicitudes nadie las firma y por
        ese camino la compra jamas llegaria a Telegram. Con este boton, quien
        captura el importe pide el visto bueno de forma explicita."""
=======
        El disparo normal vive en action_head_approve, pero hoy buena parte de
        la gente no tiene jefe: esas solicitudes pasan directo a 'Enviada' sin
        que nadie firme, y por ese camino la compra jamas llegaria a Telegram.
        Con este boton, quien captura el importe pide el visto bueno de forma
        explicita."""
>>>>>>> origin/main
        if not (self.env.user.has_group(
                'amunet_compras_general.group_compras_monto')
                or self.env.user.has_group(
                    'amunet_material_request.group_material_manager')):
            raise UserError(_(
                'Solo el area de compras puede pedir la autorizacion de pago.'))
        for req in self:
            if not req.amunet_forma_pago:
                raise UserError(_(
                    'Falta la forma de pago en %s.\n\nSin ese dato no se sabe '
                    'si la compra se hace en la tienda o si va al grupo de '
                    'pagos por transferencia.') % req.name)
            if not req.sudo().amunet_monto:
                raise UserError(_(
                    'Falta el importe en %s.\n\nNo se puede pedir una '
                    'autorizacion de pago sin decir cuanto.') % req.name)
            if req.amunet_autorizacion_estado not in ('na', False):
                raise UserError(_(
                    '%s ya esta en el circuito de autorizacion (%s).')
                    % (req.name, req.amunet_autorizacion_estado))
        self._amunet_encolar_autorizacion()
        return True

<<<<<<< HEAD
    def action_autorizar(self):
        """Primera firma (jefe directo). Si la compra ya trae forma de pago,
        se encola la segunda: el visto bueno de Fernando por Telegram."""
        resultado = super().action_autorizar()
        for req in self:
            if not req.amunet_forma_pago:
=======
    def action_head_approve(self):
        resultado = super().action_head_approve()
        for req in self:
            if req.request_type != 'general' or not req.amunet_forma_pago:
>>>>>>> origin/main
                continue
            if req.amunet_autorizacion_estado not in ('na', False):
                continue
            req._amunet_encolar_autorizacion()
        return resultado
