# -*- coding: utf-8 -*-
"""El secreto HMAC tiene que existir ANTES del primer boton.

Se generaba solo cuando Odoo firmaba algo, pero quien firma es el servicio
amunet-pagos-bot, que solo lee. Resultado: en una instalacion nueva el
primer aviso fallaba hasta que alguien generaba el secreto a mano. Se crea
aqui, al instalar."""


def post_init_generar_secreto(env):
    env['amunet.material.request']._amunet_hmac_secret()
