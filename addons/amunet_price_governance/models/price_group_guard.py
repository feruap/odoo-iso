# -*- coding: utf-8 -*-
"""Candado de gobierno del grupo "Amunet / Ver precios".

Ver la descripcion larga en __manifest__.py.

Estrategia: en lugar de intentar interpretar los comandos x2many de
``vals`` (que pueden ser (4,id), (3,id), (6,0,[...]), (5,) y ademas
propagarse por grupos implicados), se toma una FOTO de los miembros
efectivos del grupo antes de la operacion, se deja que la operacion se
ejecute, y se compara despues. Si la membresia cambio y quien opera no
esta autorizado, se lanza UserError: la excepcion revierte toda la
transaccion, de modo que el cambio nunca llega a la base de datos.
"""

import logging

from odoo import api, models, SUPERUSER_ID, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

PRICE_GROUP_XMLID = 'amunet_price_visibility.group_price_viewer'

# Unico usuario autorizado a decidir quien ve precios.
OWNER_LOGIN = 'fernando.ruiz@amunet.com.mx'

# Escape explicito para scripts autorizados (mismo patron que
# 'amunet_alta_autorizada' en amunet_warehouse_access).
CTX_AUTORIZADO = 'amunet_precio_autorizado'

_MSG_BLOQUEADO = (
    "Cambio bloqueado por el candado de precios de Amunet.\n\n"
    "La membresia del grupo \"Amunet / Ver precios\" solo puede modificarla "
    "%(owner)s. Ser administrador de Odoo NO alcanza: esta restriccion esta "
    "escrita en el codigo del sistema, no en los permisos.\n\n"
    "El intento quedo registrado (usuario: %(login)s).\n\n"
    "Si el cambio es legitimo, pidaselo a %(owner)s."
) % {'owner': OWNER_LOGIN, 'login': '%(login)s'}


# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------

def _price_group(env):
    return env.ref(PRICE_GROUP_XMLID, raise_if_not_found=False)


def _guard_enabled(env):
    """El candado no actua durante instalacion/actualizacion de modulos
    (ahi corren los datos semilla del propio amunet_price_visibility) ni
    cuando un script pide autorizacion explicita por contexto."""
    return env.registry.ready and not env.context.get(CTX_AUTORIZADO)


def _snapshot(env):
    """Conjunto de ids de usuario que efectivamente ven precios."""
    group = _price_group(env)
    if not group:
        return None
    env.invalidate_all()
    return frozenset(group.sudo().all_user_ids.ids)


def _bitacora(env, nivel, mensaje):
    """Deja constancia en ir.logging con un cursor propio, para que el
    registro sobreviva al rollback provocado por el UserError."""
    try:
        with env.registry.cursor() as cr_alarma:
            api.Environment(cr_alarma, SUPERUSER_ID, {})['ir.logging'].create({
                'name': 'amunet.price.guard',
                'type': 'server',
                'dbname': cr_alarma.dbname,
                'level': nivel,
                'message': mensaje,
                'path': 'amunet_price_governance',
                'func': 'price_group_guard',
                'line': '0',
            })
    except Exception:  # nunca dejar que la bitacora rompa la operacion
        _logger.exception('AMUNET_PRICE_GUARD: no se pudo escribir la bitacora')


def _describe(env):
    user = env.user
    return 'uid=%s login=%s su=%s' % (user.id, user.login, env.su)


def _check(env, antes, operacion):
    """Compara la foto previa con la actual y decide."""
    if antes is None:
        return
    despues = _snapshot(env)
    if despues is None or despues == antes:
        return

    agregados = sorted(despues - antes)
    quitados = sorted(antes - despues)
    detalle = 'operacion=%s agregados=%s quitados=%s por %s' % (
        operacion, agregados, quitados, _describe(env),
    )

    autorizado = (not env.su) and env.user.login == OWNER_LOGIN
    if autorizado:
        _logger.warning('AMUNET_PRICE_GUARD cambio autorizado: %s', detalle)
        _bitacora(env, 'WARNING', 'Cambio AUTORIZADO en el grupo Ver precios: %s' % detalle)
        return

    _logger.warning('AMUNET_PRICE_GUARD BLOQUEADO: %s', detalle)
    _bitacora(env, 'ERROR', 'Intento BLOQUEADO de cambiar el grupo Ver precios: %s' % detalle)
    raise UserError(_(_MSG_BLOQUEADO) % {'login': env.user.login})


# ---------------------------------------------------------------------------
# res.users
# ---------------------------------------------------------------------------

_USER_TRIGGERS = ('group_ids', 'all_group_ids', 'active')


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        if not _guard_enabled(self.env):
            return super().create(vals_list)
        antes = _snapshot(self.env)
        registros = super().create(vals_list)
        _check(self.env, antes, 'res.users.create')
        return registros

    def write(self, vals):
        if not _guard_enabled(self.env) or not any(f in vals for f in _USER_TRIGGERS):
            return super().write(vals)
        antes = _snapshot(self.env)
        resultado = super().write(vals)
        _check(self.env, antes, 'res.users.write')
        return resultado

    def unlink(self):
        if not _guard_enabled(self.env):
            return super().unlink()
        antes = _snapshot(self.env)
        resultado = super().unlink()
        # borrar un usuario que veia precios reduce la membresia: es un
        # cambio, pero no una fuga. Solo se registra.
        despues = _snapshot(self.env)
        if antes is not None and despues is not None and despues != antes:
            _bitacora(self.env, 'WARNING',
                      'Usuario(s) con acceso a precios eliminados por %s' % _describe(self.env))
        return resultado


# ---------------------------------------------------------------------------
# res.groups
# ---------------------------------------------------------------------------

_GROUP_TRIGGERS = ('user_ids', 'implied_ids', 'implied_by_ids', 'all_implied_ids',
                   'all_implied_by_ids', 'all_user_ids')


class ResGroups(models.Model):
    _inherit = 'res.groups'

    @api.model_create_multi
    def create(self, vals_list):
        if not _guard_enabled(self.env):
            return super().create(vals_list)
        antes = _snapshot(self.env)
        registros = super().create(vals_list)
        _check(self.env, antes, 'res.groups.create')
        return registros

    def write(self, vals):
        if not _guard_enabled(self.env) or not any(f in vals for f in _GROUP_TRIGGERS):
            return super().write(vals)
        antes = _snapshot(self.env)
        resultado = super().write(vals)
        _check(self.env, antes, 'res.groups.write')
        return resultado

    def unlink(self):
        if not _guard_enabled(self.env):
            return super().unlink()
        grupo = _price_group(self.env)
        if grupo and grupo.id in self.ids:
            _bitacora(self.env, 'ERROR',
                      'Intento BLOQUEADO de ELIMINAR el grupo Ver precios por %s'
                      % _describe(self.env))
            raise UserError(_(
                "No se puede eliminar el grupo \"Amunet / Ver precios\".\n\n"
                "Es el candado que oculta los importes en todo el sistema. "
                "Solo %s puede retirarlo, y para eso hay que desinstalar el "
                "modulo, no borrar el grupo."
            ) % OWNER_LOGIN)
        antes = _snapshot(self.env)
        resultado = super().unlink()
        _check(self.env, antes, 'res.groups.unlink')
        return resultado
