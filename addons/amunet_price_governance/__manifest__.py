# -*- coding: utf-8 -*-
{
    'name': 'Amunet - Gobierno del candado de precios',
    'summary': 'Nadie salvo Fernando puede alterar quien ve precios; todo intento queda registrado.',
    'description': """
El modulo amunet_price_visibility decide QUIEN ve precios: los miembros del
grupo "Amunet / Ver precios". Pero cualquier usuario con permiso de
"Access Rights" (base.group_erp_manager, implicado por base.group_system)
podia agregarse a si mismo a ese grupo desde Ajustes > Usuarios.

Este modulo cierra esa puerta a nivel de CODIGO, que las reglas de acceso de
Odoo no pueden anular:

  1. Ningun usuario -- ni administrador, ni superusuario, ni un proceso
     automatico -- puede agregar o quitar miembros del grupo "Ver precios".
     Solo el propietario del candado (Fernando) puede hacerlo desde la
     interfaz, o un script explicitamente autorizado con el contexto
     'amunet_precio_autorizado'.

  2. Tampoco se puede llegar al grupo por la puerta de atras: se bloquea
     crear o modificar otro grupo para que "implique" el grupo de precios,
     y se bloquea borrar o vaciar el grupo de precios.

  3. Todo cambio autorizado y todo intento bloqueado se registra en
     Ajustes > Tecnico > Registro de la base de datos (ir.logging) con el
     nombre 'amunet.price.guard', usando un cursor independiente para que
     el registro sobreviva aunque la operacion se revierta.

LIMITE HONESTO: mientras un usuario conserve base.group_system puede
desinstalar este modulo desde Aplicaciones (queda registrado, pero puede).
La proteccion es completa unicamente para usuarios SIN base.group_system.
""",
    'author': 'Amunet',
    'category': 'Hidden',
    'version': '19.0.1.0.0',
    'depends': [
        'base',
        'amunet_price_visibility',
    ],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',
}
