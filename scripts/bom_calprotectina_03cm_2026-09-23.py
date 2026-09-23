# La receta de CALPROTECTINA (DMCAL01) lleva 0.4 cm de hoja maestra por pieza y
# debe llevar 0.3. Cambio pedido por Mery el 23-sep-2026.
#
# El rendimiento de la hoja se lee de los CM del BoM, nunca del nombre del
# producto: 0.3 y 0.4 son los dos valores validos segun el producto, asi que
# esto es un ajuste deliberado, no una correccion de dato.
#
# Se actualiza tambien la orden viva 0926/02/CAL, que esta en borrador: las
# ordenes ya explotadas conservan la cantidad con la que nacieron y no se
# recalculan solas al cambiar la receta.
CLAVE_HOJA = 'SPHMC55'
NUEVO = 0.3

Bom = env['mrp.bom']
bom = Bom.search([('product_tmpl_id.default_code', '=', 'DMCAL01'), ('active', '=', True)], limit=1)
assert bom, 'No se encontro la receta activa de DMCAL01'
linea = bom.bom_line_ids.filtered(lambda l: l.product_id.default_code == CLAVE_HOJA)
assert len(linea) == 1, 'Se esperaba UNA linea de %s, hay %s' % (CLAVE_HOJA, len(linea))
anterior = linea.product_qty
if anterior == NUEVO:
    print('la receta ya estaba en %s cm' % NUEVO)
else:
    linea.product_qty = NUEVO
    print('receta %s: %s -> %s cm por pieza' % (bom.id, anterior, NUEVO))

# --- la orden viva ---
MO = env['mrp.production']
for mo in MO.search([('product_id.default_code', '=', 'DMCAL01'),
                     ('state', 'not in', ('done', 'cancel'))]):
    mv = mo.move_raw_ids.filtered(lambda m: m.product_id.default_code == CLAVE_HOJA
                                  and m.state not in ('done', 'cancel'))
    if not mv:
        print('  %s: sin linea de %s' % (mo.name, CLAVE_HOJA)); continue
    esperado = (mo.product_qty or 0.0) * NUEVO
    for m in mv:
        antes = m.product_uom_qty
        if antes == esperado:
            print('  %s: ya estaba en %s cm' % (mo.name, esperado)); continue
        m.product_uom_qty = esperado
        print('  %s (%s, %s pz): %s -> %s cm' % (mo.name, mo.state, mo.product_qty, antes, esperado))
    mo.message_post(body=(
        'Receta ajustada: la hoja maestra pasa de %s a %s cm por pieza. '
        'La orden se actualizo a %s cm. Cambio pedido por Mery, 23-sep-2026.'
    ) % (anterior, NUEVO, esperado))

env.cr.commit()
print('\n--- como queda ---')
for l in bom.bom_line_ids.sorted('sequence'):
    print('  %-10s %8s %s' % (l.product_id.default_code, l.product_qty, l.product_uom_id.name))
for mo in MO.search([('product_id.default_code', '=', 'DMCAL01'), ('state', 'not in', ('done', 'cancel'))]):
    for m in mo.move_raw_ids.filtered(lambda x: x.product_id.default_code == CLAVE_HOJA):
        print('  %s -> %s %s de %s' % (mo.name, m.product_uom_qty, m.product_uom.name, CLAVE_HOJA))
