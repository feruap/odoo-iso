# -*- coding: utf-8 -*-
"""Meter a Fernando en "Compras / Captura de pagos" DESPUES de subir la v19.0.6.0.0.

POR QUE HACE FALTA UN PASO A MANO
El modulo trae security/usuarios_pagos.xml, que mete a Fernando en el grupo,
dentro de un bloque <data noupdate="1">. Ese bloque corre en la INSTALACION,
no en un update. Como amunet_compras_general ya esta instalado en produccion
(v19.0.5.0.0), subir la v6.0.0 es un update: el archivo se salta y el grupo
"Captura de pagos" se crea VACIO. Nadie puede anotar un pago.

Se detecto validando la v6.0.0 sobre un clon de produccion el 24-sep-2026, antes
de subirla: el grupo aparecio sin un solo miembro.

POR QUE ASI Y NO CAMBIANDO EL noupdate A 0
Con noupdate="0" el archivo se re-aplicaria en cada actualizacion del modulo y
pisaria la membresia real: si manana se agrega o se quita a alguien desde la
pantalla de usuarios, el siguiente update lo revierte sin avisar. El noupdate="1"
esta puesto a proposito -- lo dice el comentario del propio archivo -- y la
decision de Mery (24-sep-2026) fue respetarlo y dar el acceso a mano.

CUANDO CORRERLO
Una sola vez, justo despues del deploy de la v19.0.6.0.0 a produccion.
Idempotente: si Fernando ya esta en el grupo, no hace nada.
"""

G = env['res.groups'].sudo()
U = env['res.users'].sudo()

grupo = env.ref('amunet_compras_general.group_compras_pagos', raise_if_not_found=False)
if not grupo:
    print('  el grupo no existe todavia: falta subir la v19.0.6.0.0')
else:
    fer = U.search([('login', '=', 'fernando.ruiz@amunet.com.mx')], limit=1)
    assert fer, 'no encuentro al usuario de Fernando'
    campo = 'user_ids' if 'user_ids' in G._fields else 'users'
    if fer in grupo[campo]:
        print('  %s ya estaba en "%s"' % (fer.name, grupo.name))
    else:
        grupo.write({campo: [(4, fer.id)]})
        print('  agregado %s a "%s"' % (fer.name, grupo.name))
    env.flush_all()
    print('  miembros ahora: %s' % (', '.join(grupo[campo].mapped('name')) or 'ninguno'))
    # el grupo implica ver montos; se confirma que no metio a nadie mas
    gm = env.ref('amunet_compras_general.group_compras_monto')
    print('  ven montos de compra general: %s' % ', '.join(gm[campo].mapped('name')))
    env.cr.commit()
