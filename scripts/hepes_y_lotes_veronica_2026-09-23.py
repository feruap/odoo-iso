# Dos cosas que confirmo Karla (Almacen MP) el 23-sep-2026, autorizadas por Mery.
#
# 1. HEPES lote REC20032501, 15 g: NO existe fisicamente. Karla lo conto. Es el
#    primero de los 19 lotes que se cargaron el 1-ago-2026 a las 00:06 sin
#    ningun movimiento, o sea sin trazabilidad de donde salieron.
#
# 2. IPTG y DTT: el material llego en DICIEMBRE de 2025, lo recibio y entrego
#    Veronica Ortiz, y AMP nunca lo tuvo. Los lotes en sistema dicen 062601
#    (junio 2026), que es una fecha que no corresponde. Se renombran a 122501,
#    la nomenclatura del resto de esa remesa. NO se descargan las existencias:
#    el material existe, esta en otra area, y borrarlo de los libros lo dejaria
#    sin respaldo si aparece. Eso se decide aparte.
#    Verificado: ninguno de los dos lotes tiene analisis de calidad.
L = env['stock.lot']
Q = env['stock.quant']

# --- 1. HEPES a cero ---
MOTIVO_HEPES = ('Ajuste 23-sep-2026: 15 g de HEPES que el sistema tenia sin un '
                'solo movimiento (carga directa del 1-ago-2026). Karla Palma '
                'conto fisicamente y NO existen. Autorizado por Mery.')
lot = L.search([('name', '=', 'REC20032501')], limit=1)
assert lot, 'No existe el lote REC20032501'
quants = Q.search([('lot_id', '=', lot.id), ('quantity', '!=', 0),
                   ('location_id.usage', '=', 'internal')])
pz = sum(quants.mapped('quantity'))
if pz:
    quants.with_context(inventory_mode=True).write(
        {'inventory_quantity': 0.0, 'inventory_diff_quantity': -pz})
    quants.with_context(inventory_mode=True).action_apply_inventory()
    lot.message_post(body=MOTIVO_HEPES)
    print('HEPES: descontados %s g del lote %s' % (pz, lot.name))
else:
    print('HEPES: el lote ya estaba en cero')

# --- 2. renombrar los lotes de Veronica ---
NOTA = ('Lote renombrado el 23-sep-2026: el material llego en DICIEMBRE de 2025 '
        'y lo recibio y entrego Veronica Ortiz; el numero anterior (062601) '
        'indicaba junio de 2026, que no corresponde. Se alinea con la '
        'nomenclatura del resto de esa remesa. Reportado por Karla Palma. '
        'La existencia NO se toca: el material existe, esta fuera de AMP.')
RENOMBRES = [('REC25062601', 'REC25122501', 'MPREC25 IPTG'),
             ('REC26062601', 'REC26122501', 'MPREC26 DTT')]
for viejo, nuevo, quien in RENOMBRES:
    lote = L.search([('name', '=', viejo)], limit=1)
    if not lote:
        print('  %s no existe' % viejo); continue
    chk = env['amunet.quality.check'].with_context(active_test=False).search_count(
        [('lot_id', '=', lote.id)])
    assert chk == 0, 'El lote %s tiene %s analisis, no se renombra' % (viejo, chk)
    ocupado = L.search([('name', '=', nuevo), ('product_id', '=', lote.product_id.id)], limit=1)
    assert not ocupado, 'El lote %s ya existe para ese producto' % nuevo
    lote.write({'name': nuevo})
    lote.message_post(body=NOTA)
    print('  %-12s -> %-12s  (%s)' % (viejo, nuevo, quien))

env.cr.commit()
print('\n--- como queda ---')
for _v, nuevo, _q in RENOMBRES:
    lote = L.search([('name', '=', nuevo)], limit=1)
    for q in Q.search([('lot_id', '=', lote.id), ('quantity', '!=', 0), ('location_id.usage', '=', 'internal')]):
        print('  %-9s %-14s %8s  %s' % (lote.product_id.default_code, lote.name, q.quantity, q.location_id.complete_name))
print('  HEPES REC20032501 interno: %s' % sum(Q.search([
    ('lot_id', '=', L.search([('name', '=', 'REC20032501')], limit=1).id),
    ('location_id.usage', '=', 'internal')]).mapped('quantity')))
