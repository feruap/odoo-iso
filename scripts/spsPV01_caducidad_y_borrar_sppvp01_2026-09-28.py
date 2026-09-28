"""PVP al 5%: una sola clave (SPSPV01) y con su caducidad de 3 meses.

Autorizado por Mery el 28-sep-2026: "si, borra SPPVP01 y pon la caducidad de 3
meses".

EL CASO: dos claves para la misma solucion.

    SPPVP01  "Solucion de Polivinilpirrolidona 5%"  creada el 23-sep, SOLO en
             staging. Receta: MPREC11 50 g + agua por litro. Sin movimientos.
    SPSPV01  "Solucion de PVP al 5%"                dada de alta el 28-sep con
             clave nueva de Documentacion, en staging Y produccion. MISMA receta.

Polivinilpirrolidona y PVP son lo mismo, y las dos recetas son identicas: 50 g de
MPREC11 por litro, o sea al 5%. El duplicado se creo por no revisar si la
solucion ya existia antes de pedir la clave nueva.

Se queda SPSPV01: es la que esta en los dos entornos y la que ya usa una receta.
SPPVP01 se borra -- nunca se movio, no tiene ordenes ni lotes ni existencia, y no
la usa ninguna receta -- y con eso la clave queda libre.

Ademas SPSPV01 quedo SIN caducidad; su gemela tenia 3 meses y eso es lo correcto.

Idempotente.
"""

PT = env['product.template'].sudo()
CADUCIDAD = '3 Meses'

# --- 1. la caducidad de SPSPV01
buena = PT.search([('default_code', '=', 'SPSPV01')], limit=1)
if not buena:
    print('[ojo] SPSPV01 no existe en esta base')
else:
    if (buena.amunet_expiration_text or '') == CADUCIDAD:
        print('[ya] SPSPV01 ya tiene caducidad %r' % CADUCIDAD)
    else:
        antes = buena.amunet_expiration_text
        buena.write({'amunet_expiration_text': CADUCIDAD})
        buena.message_post(body=(
            'Caducidad fijada en %s por indicacion de Mery (28-sep-2026). Antes '
            'estaba %s.' % (CADUCIDAD, repr(antes) if antes else 'vacia')))
        print('[ok] SPSPV01 caducidad %s -> %r' % (
            repr(antes) if antes else 'vacia', CADUCIDAD))

# --- 2. borrar el duplicado
vieja = PT.with_context(active_test=False).search(
    [('default_code', '=', 'SPPVP01')], limit=1)
if not vieja:
    print('[ya] SPPVP01 no existe: la clave esta libre')
else:
    prods = vieja.product_variant_ids
    pend = []
    for etiqueta, modelo, dom in (
            ('movimientos', 'stock.move', [('product_id', 'in', prods.ids)]),
            ('lineas de movimiento', 'stock.move.line', [('product_id', 'in', prods.ids)]),
            ('existencias', 'stock.quant', [('product_id', 'in', prods.ids)]),
            ('lotes', 'stock.lot', [('product_id', 'in', prods.ids)]),
            ('usada en recetas', 'mrp.bom.line', [('product_id', 'in', prods.ids)]),
            ('ordenes', 'mrp.production', [('product_id', 'in', prods.ids)]),
            ('lineas de compra', 'purchase.order.line', [('product_id', 'in', prods.ids)]),
    ):
        n = env[modelo].sudo().with_context(active_test=False).search_count(dom)
        if n:
            pend.append('%s: %s' % (etiqueta, n))
    if pend:
        print('NO SE BORRA SPPVP01, todavia tiene -> %s' % '; '.join(pend))
    else:
        # su propia receta se va con ella
        recetas = env['mrp.bom'].sudo().search([('product_tmpl_id', '=', vieja.id)])
        if recetas:
            print('   se borra tambien su receta (%s linea(s))' % len(recetas.bom_line_ids))
            recetas.unlink()
        try:
            vieja.unlink()
            print('[ok] SPPVP01 borrado: la clave queda libre')
        except Exception as e:
            print('NO SE PUDO BORRAR SPPVP01: %s' % str(e)[:200])

print('\n=== como queda ===')
for clave in ('SPSPV01', 'SPPVP01'):
    t = PT.with_context(active_test=False).search([('default_code', '=', clave)], limit=1)
    if not t:
        print('   %-9s NO EXISTE (clave libre)' % clave); continue
    print('   %-9s %-34s caducidad=%r' % (
        clave, (t.nombre_etiqueta or t.name)[:34], t.amunet_expiration_text))
    for b in env['mrp.bom'].sudo().search([('product_tmpl_id', '=', t.id)]):
        for l in b.bom_line_ids:
            print('      receta: %-9s %g %s por %g %s' % (
                l.product_id.default_code, l.product_qty, l.product_uom_id.name,
                b.product_qty, b.product_uom_id.name))

env.cr.commit()
