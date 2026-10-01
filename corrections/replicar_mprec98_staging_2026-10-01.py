# -*- coding: utf-8 -*-
"""Replicar MPREC98 (EDTA) en staging — existe en produccion y falta aqui.

POR QUE. Al armar el corte de ARU, el EDTA del inventario fisico aparecio sin
clave en el archivo. Mery pidio revisar si no existia con otro nombre antes de
pedir una clave nueva, y revisando los 153 reactivos del catalogo de PRODUCCION
resulto que SI existe: **MPREC98 "EDTA"**, creado el 23-09-2026.

Pero en STAGING no esta. Produccion tiene 105 reactivos MPREC y staging 104, y la
diferencia es exactamente este. Se creo directo en produccion y nunca bajo al
clon.

Este script lo replica en staging con la MISMA definicion que tiene en produccion,
para que el corte de ARU pueda correr igual en los dos entornos. No se invento
nada: cada campo se copio de la ficha productiva.

NO HAY QUE CORRERLO EN PRODUCCION -- alla ya existe. Es idempotente, asi que si
se corre no hace nada, pero no tiene sentido.

Idempotente.
"""
CLAVE = 'MPREC98'

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

ya = env['product.product'].with_context(active_test=False).sudo().search(
    [('default_code', '=', CLAVE)], limit=1)
if ya:
    print('%s ya existe (activo=%s). Nada que hacer.' % (CLAVE, ya.active))
else:
    g = env['uom.uom'].sudo().search([('name', '=', 'g')], limit=1)
    categ = env['product.category'].sudo().search(
        [('complete_name', '=', 'Materia prima / Reactivo')], limit=1)
    assert g and categ, 'Falta la unidad g o la categoria Materia prima / Reactivo'
    p = env['product.product'].with_context(amunet_alta_autorizada=True).create({
        'default_code': CLAVE,
        'name': 'EDTA',
        'categ_id': categ.id,
        'uom_id': g.id,
        'tracking': 'lot',
        'is_storable': True,
        'type': 'consu',
        'qc_required': False,
        'amunet_req_quality_control': True,
    })
    env.cr.commit()
    print('%s CREADO id=%s' % (CLAVE, p.id))

p = env['product.product'].sudo().search([('default_code', '=', CLAVE)], limit=1)
print('   nombre:    %s' % p.name)
print('   categoria: %s' % p.categ_id.complete_name)
print('   unidad:    %s' % p.uom_id.name)
print('   rastreo:   %s' % p.tracking)
print('   secuencia de lote: %s' % (
    p.product_tmpl_id.lot_sequence_id.prefix if p.product_tmpl_id.lot_sequence_id
    else '(sin secuencia — se crea al primer lote)'))
