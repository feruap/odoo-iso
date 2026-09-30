# -*- coding: utf-8 -*-
"""Cuarentena de 5 dias en los 12 viales + punto de control de STBBM02.

LOS 5 DIAS. Regla de Mery, 30-sep-2026: el vial se entrega, entra a cuarentena
5 dias, y hasta entonces se le genera el analisis. El numero vive en el
producto (amunet_dias_cuarentena), no en el codigo: Calidad lo sube o lo baja
sin que nadie toque el sistema, y en cero -- el default de todo el catalogo --
nada cambia.

EL PUNTO DE STBBM02. De los 12 viales, 11 ya tenian su punto de control con
parametros de cuando entraban comprados; STBBM02 era el unico sin punto. Se
copia del de STBBM01 por indicacion de Mery: es la misma solucion (SPCPR01),
solo cambia el volumen -- 0.28 ml contra 0.12 -- y el volumen no altera que se
le mide. Se le agrega el tipo de operacion "Control de calidad" a ninguno: el
analisis de estos viales no lo levanta el picking, lo levanta el cron de
cuarentena, que busca por producto.

Idempotente.
"""
DIAS = 5

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

# --- 1. los 5 dias ---------------------------------------------------------
viales = env['product.template'].search([('amunet_etapa_ll', '=', 'llenado')])
puestos = []
for tmpl in viales.sorted(lambda t: t.default_code or ''):
    if tmpl.amunet_dias_cuarentena != DIAS:
        antes = tmpl.amunet_dias_cuarentena
        tmpl.amunet_dias_cuarentena = DIAS
        puestos.append((tmpl.default_code, antes, DIAS))

# --- 2. el punto de STBBM02, copiado del de STBBM01 ------------------------
origen = env['product.product'].search([('default_code', '=', 'STBBM01')], limit=1)
destino = env['product.product'].search([('default_code', '=', 'STBBM02')], limit=1)
assert origen and destino, 'Falta STBBM01 o STBBM02'

Punto = env['amunet.quality.point']
ya = Punto.search([('product_ids', 'in', destino.id), ('active', '=', True)])
copiado = None
if ya:
    copiado = 'ya tenia punto: %s' % ', '.join(ya.mapped('name'))
else:
    base = Punto.search([('product_ids', 'in', origen.id), ('active', '=', True)], limit=1)
    assert base, 'STBBM01 no tiene punto de control del cual copiar'
    nuevo = base.copy({
        'name': destino.name,
        'product_ids': [(6, 0, [destino.id])],
    })
    copiado = 'creado %s (id %s) desde %s, con %d parametros' % (
        nuevo.name, nuevo.id, base.name, len(nuevo.parameter_ids))

env.cr.commit()

print('=' * 84)
print('DIAS DE CUARENTENA PUESTOS EN %d VIALES' % len(puestos))
for clave, antes, ahora in puestos:
    print('   %-9s %s -> %s dias' % (clave, antes, ahora))
print('-' * 84)
print('PUNTO DE CONTROL STBBM02: %s' % copiado)
print('-' * 84)
print('ESTADO FINAL:')
for tmpl in viales.sorted(lambda t: t.default_code or ''):
    p = env['product.product'].search([('product_tmpl_id', '=', tmpl.id)], limit=1)
    pts = Punto.search([('product_ids', 'in', p.id), ('active', '=', True)])
    print('   %-9s cuarentena=%s dias   punto=%s   parametros=%d' % (
        tmpl.default_code, tmpl.amunet_dias_cuarentena,
        'SI' if pts else 'NO', sum(len(x.parameter_ids) for x in pts)))
print('=' * 84)
