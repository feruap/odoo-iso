# -*- coding: utf-8 -*-
"""Desactivar la vista huerfana que traba cualquier -u en staging.

QUE ES. 'amunet_compras_general.view_solicitud_compra_form_precio' (id 3348),
creada el 30-sep-2026. Hereda del formulario de la solicitud de compra y pide el
campo 'amunet_precio_unitario' en 'amunet.solicitud.compra.line', que YA NO
EXISTE en el codigo: quedo suelta en la base cuando la solicitud de compra se
separo de amunet_compras_general y se movio a amunet_marketplace. Se quito el
archivo que la declaraba; el registro de la base se quedo.

EL EFECTO. Odoo valida las vistas activas al actualizar, asi que CUALQUIER
'odoo -u' abortaba con:

    ParseError: Field "amunet_precio_unitario" does not exist in model
    "amunet.solicitud.compra.line"

Se topo al actualizar amunet_quality el 30-sep. Nadie podia actualizar modulos
en staging.

POR QUE SE PUEDE TOCAR, SIENDO DE PRECIOS DE COMPRA. La restriccion de Fernando
prohibe que alguien distinto de el VEA precios de compras. Desactivar una vista
que los muestra va en esa misma direccion: quita una exposicion, no la crea.
Nadie gana acceso con esto. Autorizado por Mery el 30-sep-2026.

POR QUE SE DESACTIVA Y NO SE BORRA. Desactivar es reversible con un clic y basta
para desatorar el -u: Odoo no valida las vistas inactivas. Borrarla seria
definitivo sobre trabajo de otra area.

EL CAMPO NO SE TOCA. Su registro sigue en ir_model_fields y su columna sigue en
Postgres. Se reviso: la tabla tiene 5 renglones y CERO con precio, o sea la
columna esta vacia -- pero en Odoo 19 borrar un campo dispara
'ALTER TABLE ... DROP COLUMN CASCADE', y eso no lo hago yo sobre una columna de
precios de compra. Lo limpiara el propio Odoo en el siguiente -u de
amunet_compras_general, que es su trabajo normal de mantenimiento.

SOLO STAGING. Verificado: en produccion no existe ni la vista ni el campo, y el
XML de produccion no lo pide. Tampoco esta en la rama staging ni en main: vive
unicamente en esta base.

Idempotente.
"""
XMLID = 'amunet_compras_general.view_solicitud_compra_form_precio'

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

# En sudo: ir.ui.view exige el rol Administrador y la cuenta de Mery no lo
# tiene en staging (hallazgo aparte). Una vista es registro de CONFIGURACION,
# no dato de negocio; la traza de quien y por que la deja este script.
vista = env.ref(XMLID, raise_if_not_found=False)
if vista:
    vista = vista.sudo()
if not vista:
    print('La vista %s ya no existe. Nada que hacer.' % XMLID)
else:
    print('=' * 84)
    print('VISTA: %s  (id %s)' % (vista.name, vista.id))
    print('   modelo:   %s' % vista.model)
    print('   hereda de: %s (id %s)' % (vista.inherit_id.name, vista.inherit_id.id))
    print('   hijas:     %d' % env['ir.ui.view'].sudo().search_count(
        [('inherit_id', '=', vista.id)]))
    print('   acciones que la usan: %d' % env['ir.actions.act_window'].sudo().search_count(
        [('view_id', '=', vista.id)]))
    print('   activa antes: %s' % vista.active)
    if vista.active:
        vista.write({'active': False})
        print('   -> DESACTIVADA')
    else:
        print('   -> ya estaba desactivada')
    env.cr.commit()

# Comprobacion: ninguna vista ACTIVA pide ya ese campo
env.cr.execute("""
    SELECT count(*) FROM ir_ui_view
    WHERE active AND arch_db::text LIKE '%%amunet_precio_unitario%%'
""")
quedan = env.cr.fetchone()[0]
print('-' * 84)
print('vistas ACTIVAS que todavia piden amunet_precio_unitario: %d' % quedan)
print('(el campo y su columna NO se tocaron, a proposito)')
print('=' * 84)
