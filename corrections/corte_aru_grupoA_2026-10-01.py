# -*- coding: utf-8 -*-
"""CORTE DE INVENTARIO DE ARU — grupo A: los que ya tienen lote Amunet.

QUE ES. El 21-sep-2026 se hizo el "Cierre de ARU previo al arranque formal de
Soluciones": 37 movimientos que vaciaron ARU/Stock a ajuste de inventario, a
proposito, para arrancar limpio. El material fisico se quedo en el anaquel. Este
corte reconoce en el sistema lo que hoy esta FISICAMENTE en ARU.

DE DONDE SALEN LOS DATOS. Archivo "Inventario Reactivos de soluciones (5).xlsx"
que Mery subio por Discuss el 1-oct-2026 (adjunto 11128 en staging), hoja
"Revisar": los reactivos que YA tienen lote Amunet.

POR QUE AJUSTE Y NO TRASLADO DESDE AMP. Diez de estos lotes tambien tienen
existencia en AMP/Existencias. Mery confirmo el 1-oct-2026 que **los numeros de
AMP ya EXCLUYEN lo que esta en ARU: son cantidades aparte**. Con eso el
mecanismo correcto es el ajuste de inventario en ARU, sumando. Un traslado le
quitaria a Materia Prima material que si tiene en su anaquel.

Si fuera al contrario -- si AMP incluyera lo de ARU -- habria que hacer traslado
o el mismo material quedaria contado dos veces. Esa pregunta se hizo antes de
tocar nada porque es la diferencia entre un inventario correcto y uno doble.

VA POR INVENTARIO, NO POR ESCRITURA DIRECTA: inventory_quantity +
action_apply_inventory(), para que quede el movimiento de ajuste auditable con
su fecha y su responsable.

NO SE TOCAN LAS CADUCIDADES. Los 15 lotes ya existen con su fecha en el sistema.
Este corte es de CANTIDAD. Algunas difieren de las del archivo y se reportan al
final para que Karla las revise, pero no se cambian aqui: alargar la caducidad de
un lote es otro acto, con otra autorizacion.

CHAPS QUEDA FUERA, a proposito. Su lote REC23062601 pertenece a MPREC23-DUP, un
producto DUPLICADO Y ARCHIVADO (de los que generan las ordenes de compra cuando
falta el codigo del proveedor), y ese duplicado esta en 'Units' mientras el
bueno, MPREC23, esta en gramos. Meter 6 g a un producto muerto y con la unidad
equivocada seria crear basura. Necesita decision aparte.

Idempotente: si el quant ya tiene la cantidad, no hace nada.
"""
import csv, io, re

UBICACION = 'ARU/Stock'
EXCLUIR = ('REC23062601',)   # CHAPS, ver arriba

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

aru = env['stock.location'].sudo().search(
    [('complete_name', '=', UBICACION), ('usage', '=', 'internal')], limit=1)
assert aru, 'No existe la ubicacion %s' % UBICACION

filas = [f for f in csv.DictReader(io.open('/tmp/aru_filas.csv', encoding='utf-8'))
         if f['hoja'] == 'Revisar']

aplicados, ya_estaban, saltados, caducidades = [], [], [], []
for f in filas:
    lote_nom, clave = f['lote_am'], f['clave']
    if lote_nom in EXCLUIR:
        saltados.append((clave, lote_nom, 'excluido a proposito (ver cabecera)'))
        continue
    m = re.match(r'^\s*([\d.,]+)\s*(\S*)', f['cant'] or '')
    if not m:
        saltados.append((clave, lote_nom, 'no pude leer la cantidad %r' % f['cant']))
        continue
    cantidad = float(m.group(1).replace(',', ''))
    uom_arch = (m.group(2) or '').strip()

    l = env['stock.lot'].sudo().search([('name', '=', lote_nom)], limit=1)
    if not l:
        saltados.append((clave, lote_nom, 'el lote no existe'))
        continue
    p = l.product_id
    if p.default_code != clave:
        saltados.append((clave, lote_nom, 'el lote es de %s' % (p.default_code or '?')))
        continue
    if uom_arch and uom_arch != p.uom_id.name:
        saltados.append((clave, lote_nom, 'unidad %s, el producto esta en %s' % (
            uom_arch, p.uom_id.name)))
        continue

    # caducidad: solo se reporta la diferencia, no se toca
    if f['cad'] and l.expiration_date and str(l.expiration_date)[:10] != f['cad']:
        caducidades.append((clave, lote_nom, str(l.expiration_date)[:10], f['cad']))

    q = env['stock.quant'].sudo().search([
        ('product_id', '=', p.id), ('location_id', '=', aru.id), ('lot_id', '=', l.id)], limit=1)
    antes = q.quantity if q else 0.0
    if abs(antes - cantidad) < 0.0001:
        ya_estaban.append((clave, lote_nom, cantidad, p.uom_id.name))
        continue
    if q:
        q.with_context(inventory_mode=True).inventory_quantity = cantidad
        q.with_context(inventory_mode=True).action_apply_inventory()
    else:
        nq = env['stock.quant'].sudo().with_context(inventory_mode=True).create({
            'product_id': p.id, 'location_id': aru.id, 'lot_id': l.id,
            'inventory_quantity': cantidad})
        nq.action_apply_inventory()
    aplicados.append((clave, lote_nom, antes, cantidad, p.uom_id.name, f['reactivo']))

env.cr.commit()

print('=' * 104)
print('CORTE DE ARU — GRUPO A (los que ya tienen lote Amunet)')
print('=' * 104)
print('APLICADOS: %d' % len(aplicados))
for clave, lote, antes, ahora, uom, nombre in aplicados:
    print('   %-9s %-13s %-28s %8.2f -> %8.2f %s' % (
        clave, lote, nombre[:28], antes, ahora, uom))
if ya_estaban:
    print('-' * 104)
    print('YA ESTABAN CON LA CANTIDAD CORRECTA: %d' % len(ya_estaban))
    for clave, lote, c, u in ya_estaban:
        print('   %-9s %-13s %8.2f %s' % (clave, lote, c, u))
if saltados:
    print('-' * 104)
    print('NO SE TOCARON: %d' % len(saltados))
    for clave, lote, motivo in saltados:
        print('   %-9s %-13s %s' % (clave, lote, motivo))
if caducidades:
    print('-' * 104)
    print('CADUCIDADES QUE DIFIEREN (no se cambiaron, revisar con Karla): %d' % len(caducidades))
    for clave, lote, sis, arch in caducidades:
        print('   %-9s %-13s sistema %s   archivo %s' % (clave, lote, sis, arch))
print('-' * 104)
print('COMO QUEDA ARU/Stock:')
env.cr.execute("""
    SELECT pp.default_code, COALESCE(l.name,'-'), q.quantity, u.name->>'en_US'
    FROM stock_quant q
    JOIN product_product pp ON pp.id=q.product_id
    JOIN product_template pt ON pt.id=pp.product_tmpl_id
    JOIN uom_uom u ON u.id=pt.uom_id
    LEFT JOIN stock_lot l ON l.id=q.lot_id
    JOIN stock_location sl ON sl.id=q.location_id
    WHERE sl.complete_name=%s AND q.quantity<>0
    ORDER BY 1
""", (UBICACION,))
tot = 0
for clave, lote, cant, uom in env.cr.fetchall():
    tot += 1
    print('   %-9s %-13s %10.2f %s' % (clave, lote, cant, uom))
print('   --- %d renglones en ARU/Stock' % tot)
print('=' * 104)
