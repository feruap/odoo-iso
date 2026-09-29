"""QC/2026/00514 (DMATB01): las 60 pz que Calidad devuelve salen de Desechos.

Pedido por Mery el 29-sep-2026: "en este analisis no pusieron la cantidad de material que
regresa calidad, ponle 60 pzas".

QUE PASO, todo hoy mismo:
    19:47  se fabrican 1,115 pz del lote 0926/01/TUB  ->  APT/Almacen Temporal PT
    21:53  salen 80 pz de muestra                     ->  APT/Control de calidad
    22:20  esas 80 pz se van COMPLETAS                ->  Desechos

El campo 'Cantidad a devolver' quedo en 0, y la disposicion del analisis calcula el
desecho asi:  a_desechar = muestra - a_devolver = 80 - 0 = 80.

Pero la prueba es NO DESTRUCTIVA y solo se analizaron 20. Las otras 60 nunca se
consumieron: estan fisicamente buenas, tiradas en Desechos por un cero. Y los numeros
cuadran solos: 80 de muestra - 60 que regresan = 20 desechadas = exactamente las
analizadas.

POR ESO NO BASTA CORREGIR EL CAMPO. Escribir 60 sin mover el material deja el analisis
diciendo que devolvio 60 y el inventario diciendo que se desecharon 80. Se hacen las dos
cosas: el dato y el regreso fisico de las 60 pz a APT/Almacen Temporal PT, que es de donde
salieron.

EL ANALISIS ESTA FIRMADO Y CERRADO (Realizo Rodrigo, Verifico Diana, Autorizo la RS), asi
que el cambio pasa por change_reason y queda en el chatter. Se pudo hacer porque el LOTE
todavia no esta liberado y su snapshot DHR no esta sellado: no hay registro inmutable que
quede contradicho. Si el lote ya estuviera liberado, esto NO se haria por aqui.

Idempotente: si el campo ya dice 60 y las 60 pz ya no estan en Desechos, no hace nada.
"""
from markupsafe import Markup

Check = env['amunet.quality.check'].sudo()
Quant = env['stock.quant'].sudo()

qc = Check.browse(943)
assert qc.exists() and qc.name == 'QC/2026/00514', 'el id 943 no es QC/2026/00514'
lote = qc.lot_id
prod = qc.product_id
CANT = 60.0

print('=== %s  %s  lote %s ===' % (qc.name, prod.default_code, lote.name))
print('   muestra %s   analizada %s   a devolver (antes) %s   destructiva=%s' % (
    qc.qty_sampling, qc.qty_analyzed, qc.qty_to_return, qc.test_destructiveness))

# blindaje: el lote no debe estar liberado, o el snapshot DHR quedaria contradicho
if lote.amunet_lot_release_state == 'released':
    raise Exception('El lote ya esta liberado y su snapshot DHR esta sellado; '
                    'esta correccion no va por aqui.')

# ---- 1. el dato del analisis ----
if abs((qc.qty_to_return or 0.0) - CANT) < 0.001:
    print('   [ya] el campo ya dice %s' % CANT)
else:
    qc.write({
        'qty_to_return': CANT,
        'change_reason': (
            'Correccion autorizada por Mery el 29-sep-2026: la cantidad a devolver quedo '
            'en 0 al capturar y la prueba es NO destructiva. De las 80 pz de muestra solo '
            'se analizaron 20, asi que Calidad devuelve 60. El cero hizo que la '
            'disposicion mandara las 80 a Desechos; las 60 buenas se regresan a '
            'APT/Almacen Temporal PT en el mismo acto.'),
    })
    print('   [ok] a devolver: 0 -> %s' % CANT)

# ---- 2. las 60 pz salen de Desechos ----
desechos = env.ref('stock.stock_location_scrapped')
destino = env['stock.location'].sudo().search(
    [('complete_name', '=', 'APT/Almacén Temporal PT')], limit=1)
assert destino, 'no se encontro APT/Almacen Temporal PT'

en_desechos = sum(Quant.search([('product_id', '=', prod.id), ('lot_id', '=', lote.id),
                                ('location_id', '=', desechos.id)]).mapped('quantity'))
print('   en Desechos ahora: %s pz' % en_desechos)

if en_desechos < CANT - 0.001:
    print('   [ya] en Desechos quedan %s pz: las 60 ya se regresaron antes' % en_desechos)
else:
    # en Odoo 19 stock.move ya no tiene campo 'name': la descripcion va en
    # description_picking y el vinculo al analisis en origin
    mov = env['stock.move'].sudo().create({
        'description_picking': 'Devolución de muestra no consumida %s' % qc.name,
        'product_id': prod.id,
        'product_uom_qty': CANT,
        'product_uom': prod.uom_id.id,
        'location_id': desechos.id,
        'location_dest_id': destino.id,
        'origin': qc.name,
        'company_id': qc.company_id.id or env.company.id,
    })
    mov._action_confirm()
    mov._action_assign()
    mov.move_line_ids.unlink()
    env['stock.move.line'].sudo().create({
        'move_id': mov.id,
        'product_id': prod.id,
        'lot_id': lote.id,
        'quantity': CANT,
        'product_uom_id': prod.uom_id.id,
        'location_id': desechos.id,
        'location_dest_id': destino.id,
        'picked': True,
    })
    mov._action_done()
    print('   [ok] %s: %s pz  Desechos -> %s' % (mov.reference or mov.id, CANT, destino.complete_name))
    qc.message_post(body=Markup(
        'Corrección autorizada por Mery el 29-sep-2026.<br/><br/>'
        'La <b>cantidad a devolver</b> quedó en 0 al capturar, y la disposición calcula el '
        'desecho como <i>muestra menos devolución</i>: 80 − 0 = 80. Por eso las 80 pz de '
        'muestra se fueron completas a Desechos.<br/><br/>'
        'La prueba es <b>no destructiva</b> y solo se analizaron 20 pz. Las otras 60 nunca '
        'se consumieron, así que se corrigió el campo a <b>60</b> y esas 60 pz se '
        'regresaron de Desechos a <b>%s</b>.<br/><br/>'
        'Los números cuadran: 80 de muestra − 60 devueltas = 20 desechadas, que son '
        'exactamente las analizadas.'
    ) % destino.complete_name)
    lote.message_post(body=Markup(
        '60 pz regresadas de Desechos a <b>%s</b> el 29-sep-2026, autorizado por Mery.'
        '<br/><br/>Habían salido a Desechos porque el análisis %s tenía la cantidad a '
        'devolver en 0. La prueba no es destructiva y solo se analizaron 20 de las 80 de '
        'muestra.' % (destino.complete_name, qc.name)))

print('\n=== como queda ===')
qc.invalidate_recordset()
print('   %s  a devolver = %s' % (qc.name, qc.qty_to_return))
for q in Quant.search([('product_id', '=', prod.id), ('lot_id', '=', lote.id)]):
    if abs(q.quantity) > 0.0001:
        print('   %-42s %s pz' % (q.location_id.complete_name, q.quantity))
env.cr.commit()
