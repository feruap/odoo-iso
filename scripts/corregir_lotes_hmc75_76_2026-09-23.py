# Karla (Almacen MP) reporta que las hojas SPHMC75 y SPHMC76 que entraron por
# CONV/00009 traen el lote equivocado y eso impide que Calidad las apruebe.
#
# Lo que paso el 28-ago:
#   17:27  la recepcion AMP/IN/00346 creo los lotes ...02
#   18:34  la conversion de combos invento unos ...03 duplicados (bug ya corregido)
#   18:35  CONV/00009 movio las 900 pz con los ...03
#
# Los ...02 quedaron vacios: cero movimientos, cero existencia, cero analisis.
# Por eso NO se ajusta inventario ni se inventan movimientos: se corrige el
# NOMBRE, que es lo unico que esta mal. Toda la trazabilidad se conserva.
#
# Mismo criterio que ya se uso con SPHMC70 (HMC70082601-NO-USADO).
PARES = [
    ('HMC75082603', 'HMC75082602'),   # SPHMC75 Antidoping Sangre 2 Parametros
    ('HMC76082603', 'HMC76082602'),   # SPHMC76 Antidoping Sangre 3 Parametros
]
NOTA = ('Lote renombrado a peticion de Almacen MP (Karla) el 23-sep-2026: la '
        'conversion de combos CONV/00009 genero un numero duplicado y el que '
        'corresponde al material fisico es el de la recepcion AMP/IN/00346.')

L = env['stock.lot']
for actual, correcto in PARES:
    lote = L.search([('name', '=', actual)], limit=1)
    assert lote, 'No existe el lote %s' % actual
    vacio = L.with_context(active_test=False).search([('name', '=', correcto)], limit=1)
    if vacio:
        assert env['stock.move.line'].search_count([('lot_id', '=', vacio.id)]) == 0, \
            'El lote %s SI tiene movimientos, no se toca' % correcto
        assert env['stock.quant'].search_count([('lot_id', '=', vacio.id), ('quantity', '!=', 0)]) == 0, \
            'El lote %s SI tiene existencia, no se toca' % correcto
        vacio.write({'name': '%s-NO-USADO' % correcto})
        print('  apartado  %s  -> %s-NO-USADO (estaba vacio)' % (correcto, correcto))
    lote.write({'name': correcto})
    lote.message_post(body=NOTA)
    pz = sum(env['stock.quant'].search([
        ('lot_id', '=', lote.id), ('location_id.usage', '=', 'internal')]).mapped('quantity'))
    print('  CORREGIDO %-9s %s -> %s   (%s pz)' % (lote.product_id.default_code, actual, correcto, pz))

env.cr.commit()
print('\n--- como queda ---')
for _a, correcto in PARES:
    lote = L.search([('name', '=', correcto)], limit=1)
    for q in env['stock.quant'].search([('lot_id', '=', lote.id), ('quantity', '!=', 0)]):
        print('  %-14s %-9s %8s  %s' % (lote.name, lote.product_id.default_code,
                                        q.quantity, q.location_id.complete_name))
    for c in env['amunet.quality.check'].search([('lot_id', '=', lote.id)]):
        print('      analisis %s  estado=%s' % (c.name, c.state))
