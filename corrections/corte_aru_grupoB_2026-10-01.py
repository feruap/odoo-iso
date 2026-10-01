# -*- coding: utf-8 -*-
"""CORTE DE INVENTARIO DE ARU — grupo B: los PRE-ODOO, sin lote Amunet.

QUE ES. Reactivos que estan fisicamente en el anaquel de ARU desde ANTES de que
la casa arrancara con Odoo. Nunca entraron al sistema: no tienen lote Amunet ni
movimiento de ingreso. Este corte los reconoce.

DE DONDE SALEN LOS DATOS. Archivo "Inventario Reactivos de soluciones (5).xlsx"
que Mery subio por Discuss el 1-oct-2026 (adjunto 11128 en staging), hoja
"Hoja2": el inventario fisico completo de ARU. De sus 43 renglones, 15 ya tenian
lote Amunet (grupo A, corte aparte) y estos son los que no.

POR QUE AJUSTE DE INVENTARIO. Es exactamente para lo que existe el mecanismo:
reconocer material preexistente. No hay recepcion de proveedor que replicar
-- la compra es anterior al sistema -- ni origen interno del cual trasladarlo.
Va por inventory_quantity + action_apply_inventory() para que quede el
movimiento auditable con su fecha y responsable.

QUE SE CREA POR CADA RENGLON:
  1. El lote Amunet, con el numerador de la casa (prefijo = clave sin las 2
     primeras letras + mes + anio + consecutivo: REC08102601).
  2. Su caducidad, la del archivo.
  3. El lote del PROVEEDOR, en amunet.lot.factory, ligado al lote Amunet. Es el
     unico puente con la etiqueta original del frasco, y sin el no hay forma de
     amarrar este material a su certificado de analisis.
  4. La existencia en ARU/Stock.

DOS RENGLONES DEL MISMO PRODUCTO SON DOS LOTES. MPREC07 (azida) y MPREC31
(fosfato dibasico) aparecen dos veces con lote de proveedor y caducidad
distintos: son dos envases y llevan dos lotes Amunet. MPREC09 (hidroxido de
sodio) aparece una vez aqui y otra en el grupo A: tambien son dos envases, uno ya
registrado y otro no.

MPREC84 QUEDA FUERA, a proposito. El archivo lo pone como "Agua Peptonada
Amortiguadora, 15 g" pero en Odoo MPREC84 es **Agua HPLC y esta en ml**. La clave
correcta para agua peptonada es **MPREC28**, que si esta en gramos. Es un error de
clave en el archivo y no se corrige por cuenta propia: necesita que Mery lo
confirme.

CINCO NACEN VENCIDOS O AL BORDE, y es correcto que asi sea -- el semaforo de
caducidad los va a marcar en cuanto existan. Se listan al final para que Calidad
no se lleve la sorpresa.

Idempotente: si ya hay un lote de ese producto con ese lote de proveedor, no lo
duplica.
"""
import csv, io, re

from odoo import fields

UBICACION = 'ARU/Stock'
EXCLUIR_CLAVES = ('MPREC84',)   # ver cabecera

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

aru = env['stock.location'].sudo().search(
    [('complete_name', '=', UBICACION), ('usage', '=', 'internal')], limit=1)
assert aru, 'No existe %s' % UBICACION

filas = [f for f in csv.DictReader(io.open('/tmp/aru_filas.csv', encoding='utf-8'))
         if f['hoja'] == 'Hoja2' and f['clave'].lower() != 'no tiene'
         and f['lote_am'].lower() == 'no tiene']

def caducidad_valida(txt):
    """El archivo trae 'No tiene' en varios renglones; solo se acepta YYYY-MM-DD."""
    return txt if re.match(r'^\d{4}-\d{2}-\d{2}$', (txt or '').strip()) else ''

creados, ya_estaban, saltados, vencidos = [], [], [], []
hoy = fields.Date.context_today(env['stock.lot'])

for f in filas:
    clave = f['clave']
    if clave in EXCLUIR_CLAVES:
        saltados.append((clave, f['reactivo'], 'excluido: clave equivocada en el archivo'))
        continue
    m = re.match(r'^\s*([\d.,]+)\s*(\S*)', f['cant'] or '')
    if not m:
        saltados.append((clave, f['reactivo'], 'no pude leer %r' % f['cant'])); continue
    cantidad = float(m.group(1).replace(',', ''))
    uom_arch = (m.group(2) or '').strip()

    p = env['product.product'].sudo().search([('default_code', '=', clave)], limit=1)
    if not p:
        saltados.append((clave, f['reactivo'], 'el producto no existe')); continue
    tmpl = p.product_tmpl_id
    if uom_arch and uom_arch != p.uom_id.name:
        saltados.append((clave, f['reactivo'], 'unidad %s, el producto esta en %s' % (
            uom_arch, p.uom_id.name))); continue
    if tmpl.tracking != 'lot':
        saltados.append((clave, f['reactivo'], 'no se rastrea por lote')); continue

    lote_prov = (f['lote_prov'] or '').strip()
    # idempotencia: por lote de proveedor, que es lo que identifica el envase
    existente = env['stock.lot'].sudo().search([
        ('product_id', '=', p.id), ('factory_lot_id.name', '=', lote_prov)], limit=1) \
        if lote_prov else env['stock.lot'].sudo()
    if existente:
        ya_estaban.append((clave, existente.name, lote_prov, cantidad)); continue

    nombres = p.sudo()._amunet_next_lot_names(1)
    nombre_lote = nombres[0] if nombres else False
    if not nombre_lote:
        saltados.append((clave, f['reactivo'], 'no pude generar el nombre del lote')); continue

    vals = {'name': nombre_lote, 'product_id': p.id, 'company_id': env.company.id}
    cad = caducidad_valida(f['cad'])
    if cad:
        vals['expiration_date'] = cad + ' 23:59:59'
    if lote_prov:
        fab = env['amunet.lot.factory'].sudo().search([('name', '=', lote_prov)], limit=1)
        if not fab:
            fab = env['amunet.lot.factory'].sudo().create({'name': lote_prov})
        vals['factory_lot_id'] = fab.id
    lote = env['stock.lot'].sudo().create(vals)

    nq = env['stock.quant'].sudo().with_context(inventory_mode=True).create({
        'product_id': p.id, 'location_id': aru.id, 'lot_id': lote.id,
        'inventory_quantity': cantidad})
    nq.action_apply_inventory()

    creados.append((clave, f['reactivo'], lote.name, lote_prov, cantidad, p.uom_id.name, cad))
    if cad and cad <= str(hoy):
        vencidos.append((clave, lote.name, cad, 'YA VENCIDO'))
    elif cad and cad <= str(hoy)[:4] + '-12-31':
        vencidos.append((clave, lote.name, cad, 'vence este año'))

env.cr.commit()

print('=' * 110)
print('CORTE DE ARU — GRUPO B (pre-Odoo, sin lote Amunet)')
print('=' * 110)
print('LOTES CREADOS Y CARGADOS: %d' % len(creados))
print('%-9s %-30s %-13s %-18s %10s %-4s %s' % (
    'CLAVE','REACTIVO','LOTE AMUNET','LOTE PROVEEDOR','CANT','UOM','CADUCIDAD'))
for clave, nombre, lote, prov, cant, uom, cad in creados:
    print('%-9s %-30s %-13s %-18s %10.2f %-4s %s' % (
        clave, nombre[:30], lote, prov[:18], cant, uom, cad or '(sin fecha)'))
if ya_estaban:
    print('-' * 110)
    print('YA EXISTIAN (mismo producto y lote de proveedor): %d' % len(ya_estaban))
    for clave, lote, prov, cant in ya_estaban:
        print('   %-9s %-13s proveedor %s' % (clave, lote, prov))
if saltados:
    print('-' * 110)
    print('NO SE CARGARON: %d' % len(saltados))
    for clave, nombre, motivo in saltados:
        print('   %-9s %-30s %s' % (clave, nombre[:30], motivo))
if vencidos:
    print('-' * 110)
    print('NACEN VENCIDOS O AL BORDE — avisar a Calidad: %d' % len(vencidos))
    for clave, lote, cad, est in vencidos:
        print('   %-9s %-13s caduca %s   %s' % (clave, lote, cad, est))
print('-' * 110)
env.cr.execute("""
    SELECT count(*), round(sum(q.quantity)::numeric,2)
    FROM stock_quant q JOIN stock_location sl ON sl.id=q.location_id
    WHERE sl.complete_name=%s AND q.quantity<>0
""", (UBICACION,))
n, tot = env.cr.fetchone()
print('ARU/Stock queda con %s renglones' % n)
print('=' * 110)

# ---------------------------------------------------------------------------
# RENGLONES QUE EL ARCHIVO TRAIA "SIN CLAVE" PERO EL PRODUCTO SI EXISTIA
#
# Mery, 1-oct-2026: "antes de decir que no estan revisa si existen con otro
# nombre". Se reviso: por nombre, clave, etiqueta y descripcion, incluyendo
# archivados, mas la Lista de Claves de Documentacion, mas los 153 reactivos del
# catalogo uno por uno.
#
# De los 6 que el archivo traia sin clave, UNO si existia:
#     E.D.T.A  ->  MPREC98 "EDTA", activo, en gramos
#
# Los otros 5 (acetato de potasio, carbonato de potasio, acido citrico, extracto
# de levadura y glicerina) de verdad no estan: se pidieron a Documentacion con
# la instruccion de revisar antes con Karla si no existen con otro nombre.
#
# DOS TRAMPAS DE NOMBRE PARECIDO que se verificaron y NO son el mismo producto:
#   - 'Acetato de potasio' no es acetato de plomo (MPREC66) ni de litio (MPREC71).
#   - 'Acido citrico' no es citrato de sodio (MPREC01): el citrato es la sal.
# ---------------------------------------------------------------------------
RESCATADOS = [
    # (nombre en el archivo, clave encontrada, cantidad, uom, caducidad, lote proveedor)
    ('E.D.T.A', 'MPREC98', 143.0, 'g', '2028-10-01', '191023'),
]

rescates = []
for nombre, clave, cantidad, uom_esp, cad, lote_prov in RESCATADOS:
    p = env['product.product'].sudo().search([('default_code', '=', clave)], limit=1)
    if not p:
        rescates.append((clave, nombre, 'el producto no existe')); continue
    if p.uom_id.name != uom_esp:
        rescates.append((clave, nombre, 'unidad %s, esperaba %s' % (p.uom_id.name, uom_esp)))
        continue
    ya = env['stock.lot'].sudo().search([
        ('product_id', '=', p.id), ('factory_lot_id.name', '=', lote_prov)], limit=1)
    if ya:
        rescates.append((clave, nombre, 'ya existia el lote %s' % ya.name)); continue
    nombres = p.sudo()._amunet_next_lot_names(1)
    vals = {'name': nombres[0], 'product_id': p.id, 'company_id': env.company.id}
    if caducidad_valida(cad):
        vals['expiration_date'] = cad + ' 23:59:59'
    fab = env['amunet.lot.factory'].sudo().search([('name', '=', lote_prov)], limit=1)
    if not fab:
        fab = env['amunet.lot.factory'].sudo().create({'name': lote_prov})
    vals['factory_lot_id'] = fab.id
    lote = env['stock.lot'].sudo().create(vals)
    nq = env['stock.quant'].sudo().with_context(inventory_mode=True).create({
        'product_id': p.id, 'location_id': aru.id, 'lot_id': lote.id,
        'inventory_quantity': cantidad})
    nq.action_apply_inventory()
    rescates.append((clave, nombre, 'CARGADO lote %s  %.2f %s  caduca %s  prov %s' % (
        lote.name, cantidad, p.uom_id.name, cad, lote_prov)))

env.cr.commit()
print('-' * 110)
print('RESCATADOS (el archivo decia "sin clave" pero el producto ya existia):')
for clave, nombre, estado in rescates:
    print('   %-9s %-22s %s' % (clave, nombre[:22], estado))
env.cr.execute("""
    SELECT count(*) FROM stock_quant q JOIN stock_location sl ON sl.id=q.location_id
    WHERE sl.complete_name=%s AND q.quantity<>0
""", (UBICACION,))
print('ARU/Stock queda con %s renglones' % env.cr.fetchone()[0])
print('=' * 110)
