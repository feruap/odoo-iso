# -*- coding: utf-8 -*-
"""Las membranas pasan de rollos a centimetros.

!!! NO CORRER EN PRODUCCION TODAVIA (Mery, 1-oct-2026) !!!
    "lo anterior se trabajo en rollos, este seria un ajuste nuevo, por ello aun
    no lo subas a produccion".
    Corrido y verificado SOLO en staging. Falta que Mery defina como entra el
    ajuste a produccion.

EL PROBLEMA. Las tres membranas estan en `Units` y las recetas de hoja piden
`1.0000 Units` por lote de 30 cm. El sistema cree que se gasta UN ROLLO COMPLETO
por hoja. La realidad: el rollo trae 100 m y la hoja consume 0.31 cm.

Efecto medido: para 189 hojas el sistema pedia 189 rollos. Lo real son 58.6 cm,
el 0.6% de un rollo. Yo reporte "faltan 271 membranas, la unica compra con
tiempo de entrega real" -- equivocado por un factor de 32,000.

POR QUE NO SE USA amunet_contenido_envase (el mecanismo del garrafon de agua).
Porque ese campo supone un envase de tamano FIJO y Mery confirmo que hay rollos
de distinto largo. Con el producto en cm, cada recepcion entra con los
centimetros que traiga y el lote los registra: el largo variable deja de
importar.

POR QUE SE PUEDE CAMBIAR LA UNIDAD DE LOS PRODUCTOS QUE YA EXISTEN. Cambiar de
`Units` a `cm` NO convierte los numeros del historico: solo cambia la etiqueta,
asi que un movimiento que decia "10 Units" pasa a decir "10 cm". Eso reescribe
el significado de la historia, y en un entorno ISO 13485 normalmente obligaria a
crear productos nuevos.

Aqui no, y se midio antes de decidirlo: las tres membranas tienen 66 movimientos
y **CERO consumidos en produccion y CERO recepciones de proveedor**. Todo su
historico son ajustes de inventario de la carga inicial. No hay un solo lote
fabricado cuya trazabilidad dependa de esos numeros ni una factura que los
respalde.

EL AJUSTE DE EXISTENCIA VA POR INVENTARIO, NO POR ESCRITURA DIRECTA. Se usa
`inventory_quantity` + `action_apply_inventory()` para que quede el movimiento de
ajuste auditable, en vez de sobrescribir el quant a mano.

Todos los rollos actuales traen 100 m (confirmado por Mery, 1-oct-2026).

Idempotente.
"""
CM_POR_ROLLO = 10000.0      # 100 metros
CM_POR_HOJA = 0.31          # <-- EL NUMERO A CONFIRMAR: por hoja o por pieza
CLAVES = ('MPMNC01', 'MPMNC02', 'MPMNC03')

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)

cm = env['uom.uom'].sudo().search([('name', '=', 'cm')], limit=1)
assert cm, 'No existe la unidad cm'

# --- 0. fotografia previa: cuantos rollos hay en cada lote -------------------
previo = {}
for clave in CLAVES:
    p = env['product.product'].search([('default_code', '=', clave)], limit=1)
    assert p, 'No existe %s' % clave
    quants = env['stock.quant'].sudo().search([
        ('product_id', '=', p.id), ('location_id.usage', '=', 'internal'),
        ('quantity', '!=', 0)])
    previo[clave] = {'prod': p, 'uom_antes': p.uom_id.name,
                     'quants': [(q.id, q.lot_id.name or '(sin lote)', q.quantity) for q in quants]}

print('=' * 92)
print('ANTES')
for clave, d in previo.items():
    print('  %s  unidad=%s' % (clave, d['uom_antes']))
    for _qid, lote, cant in d['quants']:
        print('      lote %-14s %6.2f rollos' % (lote, cant))

# --- 1. cambiar la unidad ----------------------------------------------------
cambiadas = []
for clave, d in previo.items():
    tmpl = d['prod'].product_tmpl_id
    if tmpl.uom_id != cm:
        tmpl.sudo().write({'uom_id': cm.id})
        cambiadas.append(clave)

# --- 2. redeclarar la existencia en cm, por ajuste de inventario -------------
ajustes = []
for clave, d in previo.items():
    for qid, lote, rollos in d['quants']:
        q = env['stock.quant'].sudo().browse(qid)
        objetivo = rollos * CM_POR_ROLLO
        if abs(q.quantity - objetivo) < 0.001:
            continue
        q.with_context(inventory_mode=True).inventory_quantity = objetivo
        q.with_context(inventory_mode=True).action_apply_inventory()
        ajustes.append((clave, lote, rollos, objetivo))

# --- 3. los renglones de BoM, de 1 Unit a cm --------------------------------
renglones = []
for clave, d in previo.items():
    lineas = env['mrp.bom.line'].sudo().search([('product_id', '=', d['prod'].id)])
    for l in lineas:
        hoja = l.bom_id.product_tmpl_id.default_code or l.bom_id.display_name
        if abs(l.product_qty - CM_POR_HOJA) < 1e-9 and l.product_uom_id == cm:
            continue
        antes = '%s %s' % (l.product_qty, l.product_uom_id.name)
        l.write({'product_qty': CM_POR_HOJA, 'product_uom_id': cm.id})
        renglones.append((hoja, clave, antes))

env.cr.commit()

print('-' * 92)
print('UNIDAD CAMBIADA A cm: %s' % (', '.join(cambiadas) or 'ninguna, ya estaban'))
print('-' * 92)
print('EXISTENCIA REDECLARADA (%d lotes):' % len(ajustes))
for clave, lote, rollos, cm_final in ajustes:
    print('   %-9s lote %-14s %4.0f rollos -> %10.0f cm' % (clave, lote, rollos, cm_final))
print('-' * 92)
print('RENGLONES DE RECETA AJUSTADOS (%d):' % len(renglones))
for hoja, clave, antes in sorted(renglones):
    print('   %-9s pide %-9s  %-12s -> %s cm' % (hoja, clave, antes, CM_POR_HOJA))
print('-' * 92)
print('DESPUES:')
for clave, d in previo.items():
    p = d['prod']
    p.invalidate_recordset()
    print('   %-9s unidad=%-4s existencia=%12.0f %s  (= %.1f rollos de 100 m)' % (
        clave, p.uom_id.name, p.qty_available, p.uom_id.name,
        p.qty_available / CM_POR_ROLLO))
print('=' * 92)
