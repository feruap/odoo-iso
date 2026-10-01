# -*- coding: utf-8 -*-
"""CORTE DE ARU — los dos renglones que habian quedado fuera.

Se excluyeron del corte principal porque tenian problemas de datos y no se
resuelven adivinando. Mery los autorizo el 1-oct-2026: "ajusta CHAPS y agua
peptonada".

## 1. CHAPS — 6 g

EL PROBLEMA QUE SE VIO: el lote REC23062601 aparecia bajo MPREC23-DUP, un producto
DUPLICADO Y ARCHIVADO (de los que generan las ordenes de compra cuando falta el
codigo del proveedor), y ese duplicado esta en 'Units' mientras el bueno, MPREC23,
esta en gramos.

LO QUE RESULTO AL MIRAR MEJOR: **existen DOS lotes con el mismo nombre
REC23062601**, uno bajo el duplicado y otro bajo MPREC23, el bueno. El del
producto bueno ya existe y esta en cero. No hay que crear nada: solo cargarle los
6 g.

MI ERROR EN EL CORTE ANTERIOR: busque el lote por NOMBRE solamente
(`search([('name','=',lote)], limit=1)`) y me trajo el del duplicado. En Odoo el
nombre de lote es unico POR PRODUCTO, no global, asi que buscar por nombre sin
producto puede devolver el de otro. De aqui en adelante: siempre (nombre Y
producto).

El duplicado se queda como esta -- archivado y en cero. No se toca: borrar o
reasignar un lote con movimientos es otro acto.

## 2. Agua peptonada amortiguada — 15 g

El archivo la pone como MPREC84, pero esa clave es **Agua HPLC y esta en ml**. La
correcta es **MPREC28 "Agua peptonada amortiguada"**, que si esta en gramos. Era un
error de clave en el archivo. Se carga en MPREC28 con lote Amunet nuevo, su
caducidad y su lote de proveedor.

Idempotente.
"""
import re
from odoo import fields

UBICACION = 'ARU/Stock'
CARGAS = [
    # (clave, lote_amunet o None para generar, cantidad, uom, caducidad, lote_prov, nota)
    ('MPREC23', 'REC23062601', 6.0,  'g', '',           '75621-03-3',
     'lote ya existente bajo el producto bueno; el homonimo del duplicado no se toca'),
    ('MPREC28', None,          15.0, 'g', '2029-08-01', '512124H004',
     'el archivo decia MPREC84 (Agua HPLC, en ml); la clave correcta es MPREC28'),
]

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)
aru = env['stock.location'].sudo().search(
    [('complete_name', '=', UBICACION), ('usage', '=', 'internal')], limit=1)
assert aru, 'No existe %s' % UBICACION

hechos, problemas = [], []
for clave, lote_nom, cantidad, uom_esp, cad, lote_prov, nota in CARGAS:
    p = env['product.product'].sudo().search([('default_code', '=', clave)], limit=1)
    if not p:
        problemas.append((clave, 'el producto no existe')); continue
    if p.uom_id.name != uom_esp:
        problemas.append((clave, 'unidad %s, esperaba %s' % (p.uom_id.name, uom_esp))); continue

    if lote_nom:
        # SIEMPRE por nombre Y producto: el nombre solo es ambiguo
        l = env['stock.lot'].sudo().search([
            ('name', '=', lote_nom), ('product_id', '=', p.id)], limit=1)
        if not l:
            problemas.append((clave, 'no existe el lote %s bajo %s' % (lote_nom, clave))); continue
        creado = False
    else:
        ya = env['stock.lot'].sudo().search([
            ('product_id', '=', p.id), ('factory_lot_id.name', '=', lote_prov)], limit=1)
        if ya:
            l, creado = ya, False
        else:
            nombres = p.sudo()._amunet_next_lot_names(1)
            vals = {'name': nombres[0], 'product_id': p.id, 'company_id': env.company.id}
            if re.match(r'^\d{4}-\d{2}-\d{2}$', cad or ''):
                vals['expiration_date'] = cad + ' 23:59:59'
            if lote_prov:
                fab = env['amunet.lot.factory'].sudo().search([('name', '=', lote_prov)], limit=1)
                if not fab:
                    fab = env['amunet.lot.factory'].sudo().create({'name': lote_prov})
                vals['factory_lot_id'] = fab.id
            l = env['stock.lot'].sudo().create(vals)
            creado = True

    # el lote de proveedor tambien se liga cuando el lote ya existia y no lo traia
    if lote_prov and not l.factory_lot_id:
        fab = env['amunet.lot.factory'].sudo().search([('name', '=', lote_prov)], limit=1)
        if not fab:
            fab = env['amunet.lot.factory'].sudo().create({'name': lote_prov})
        l.sudo().factory_lot_id = fab.id

    q = env['stock.quant'].sudo().search([
        ('product_id', '=', p.id), ('location_id', '=', aru.id), ('lot_id', '=', l.id)], limit=1)
    antes = q.quantity if q else 0.0
    if abs(antes - cantidad) < 0.0001:
        hechos.append((clave, l.name, antes, cantidad, p.uom_id.name, 'ya estaba', nota))
        continue
    if q:
        q.with_context(inventory_mode=True).inventory_quantity = cantidad
        q.with_context(inventory_mode=True).action_apply_inventory()
    else:
        nq = env['stock.quant'].sudo().with_context(inventory_mode=True).create({
            'product_id': p.id, 'location_id': aru.id, 'lot_id': l.id,
            'inventory_quantity': cantidad})
        nq.action_apply_inventory()
    hechos.append((clave, l.name, antes, cantidad, p.uom_id.name,
                   'lote CREADO' if creado else 'cargado en lote existente', nota))

env.cr.commit()

print('=' * 108)
print('CHAPS Y AGUA PEPTONADA')
print('=' * 108)
for clave, lote, antes, ahora, uom, que, nota in hechos:
    print('%-9s %-14s %8.2f -> %8.2f %-3s  %s' % (clave, lote, antes, ahora, uom, que))
    print('          %s' % nota)
    l = env['stock.lot'].sudo().search([('name','=',lote),('product_id.default_code','=',clave)], limit=1)
    print('          caducidad: %s   lote de proveedor: %s' % (
        str(l.expiration_date)[:10] if l.expiration_date else '(sin fecha)',
        l.factory_lot_id.name or '(sin ligar)'))
if problemas:
    print('-' * 108)
    for clave, m in problemas:
        print('   PROBLEMA %-9s %s' % (clave, m))
print('-' * 108)
env.cr.execute("""
    SELECT count(*) FROM stock_quant q JOIN stock_location sl ON sl.id=q.location_id
    WHERE sl.complete_name=%s AND q.quantity<>0
""", (UBICACION,))
print('ARU/Stock queda con %s renglones' % env.cr.fetchone()[0])
print('=' * 108)
