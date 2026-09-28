# Renombra los lotes que Karla confirmo el 28-sep-2026 a las 15:34, uno por uno.
#
# LO QUE ELLA AUTORIZO:
#   Grupo A - controles positivos CPL: si, los 3
#   Grupo A - almohadillas SPALMA11/12/13: PENDIENTE, lo revisan despues -> NO SE TOCAN
#   Grupo B - STBTR02: se quedan como estan, decision tomada para no romper la
#             trazabilidad con los documentos de calidad ya existentes -> NO SE TOCAN
#   Grupo B - MPCAR22: en espera de verificar el lote fisico en Burgos -> NO SE TOCA
#   Grupo B - hojas maestras HMC: confirmado, son residuos, limpiar
#
# UNO NO SE PUEDE: PL04092601 (22-sep) deberia llamarse CPL04092601, pero ese
# nombre YA LO TOMO otro lote fisico distinto, creado hoy a las 16:35 -despues de
# que corregimos el prefijo, o sea el arreglo funcionando- con 27 pz y su propio
# analisis QC/2026/00511. Renombrar encima fusionaria dos lotes distintos.
# Se deja fuera y se regresa a Karla: decidir el numero correcto es suyo.
#
# Se actualiza TAMBIEN el campo lot_amunet de los analisis: guarda el nombre del
# lote como TEXTO, y sin tocarlo el analisis seguiria mostrando el nombre viejo.
# DOS RAZONES MAS por las que la lista se redujo de 8 a 4, encontradas al
# ejecutar y NO al planear:
#
# 1. UN LOTE LIBERADO NO SE RENOMBRA. amunet_quality/models/stock_lot.py lo
#    prohibe: "No se pueden modificar campos criticos de un lote liberado
#    (name). Cree un reanalisis o registre una desviacion/CAPA". Es correcto:
#    la identidad de un lote liberado quedo impresa en su expediente y en su
#    certificado. Quedan fuera PL04092602, HMC56072601 y HMC56072602.
#
# 2. UN NOMBRE OCUPADO NO SE PISA. PL04092601 (22-sep) deberia ser
#    CPL04092601, pero ese nombre lo tomo otro lote FISICO distinto creado hoy
#    a las 16:35 -con el prefijo ya corregido, o sea el arreglo funcionando-,
#    con 27 pz y analisis QC/2026/00511. Renombrar encima fusionaria dos lotes.
#
# Los tres liberados y el del nombre ocupado se regresan a Karla: decidir que
# hacer con ellos es suyo, y en los liberados el camino que marca el sistema es
# un reanalisis o una desviacion, no un renombrado.
PLAN = [
    ('STCPL14', 'PL14092601',  'CPL14092601'),
    ('SPHMC85', 'HMC18072601', 'HMC85072601'),
    ('SPHMC85', 'HMC18072602', 'HMC85072602'),
    ('SPHMC86', 'HMC62072601', 'HMC86072601'),
]

Lot = env['stock.lot'].sudo()
QC = env['amunet.quality.check'].sudo()
T = env['product.template'].sudo()
print('%-9s %-14s %-14s %s' % ('PROD', 'ANTES', 'AHORA', 'ANALISIS ACTUALIZADOS'))
for cod, act, nue in PLAN:
    t = T.search([('default_code', '=', cod)], limit=1)
    assert t, 'no existe el producto %s' % cod
    l = Lot.search([('name', '=', act), ('product_id', 'in', t.product_variant_ids.ids)], limit=1)
    if not l:
        print('%-9s %-14s %-14s el lote ya no existe con ese nombre' % (cod, act, nue)); continue
    # Guarda: el nombre destino tiene que estar LIBRE en este producto.
    choca = Lot.search([('name', '=', nue), ('product_id', 'in', t.product_variant_ids.ids)])
    assert not choca, ('%s: el nombre %s ya lo tiene el lote id=%s. NO se renombra: '
                       'serian dos lotes fisicos distintos con el mismo nombre.'
                       % (cod, nue, choca[0].id))
    # Guarda: el prefijo nuevo debe corresponder a la clave del producto.
    assert nue.startswith((cod or '')[2:]), \
        '%s: %s no empieza con el prefijo que le toca (%s)' % (cod, nue, cod[2:])
    # Guarda: un lote LIBERADO no se renombra. El propio modulo lo prohibe; se
    # comprueba aqui para que el script diga por que y no reviente a medias.
    assert getattr(l, 'amunet_lot_release_state', 'pending') != 'released', \
        ('%s (%s) esta LIBERADO: su identidad quedo en el expediente y el '
         'certificado. El camino es un reanalisis o una desviacion, no un '
         'renombrado.' % (act, cod))
    l.write({'name': nue})
    # El nombre tambien vive como texto en los analisis.
    qcs = QC.search([('lot_id', '=', l.id)])
    tocados = []
    for q in qcs:
        if 'lot_amunet' in q._fields and q.lot_amunet == act:
            q.write({'lot_amunet': nue, 'change_reason': 'Renombrado del lote %s a %s' % (act, nue)})
            tocados.append(q.name)
    l.message_post(body=(
        'Lote <b>renombrado</b> de %(a)s a %(b)s por Desarrollo.<br/><br/>'
        'El nombre no correspondia al prefijo del producto %(p)s. Confirmado por '
        'Karla (Almacen MP) el 28-sep-2026. No se movio inventario: solo cambia '
        'el nombre del registro.'
    ) % {'a': act, 'b': nue, 'p': cod})
    print('%-9s %-14s %-14s %s' % (cod, act, nue, ', '.join(tocados) or '-'))

env.cr.commit()
print()
print('=== comprobacion: cada lote empieza con el prefijo de su producto ===')
for cod, act, nue in PLAN:
    t = T.search([('default_code', '=', cod)], limit=1)
    l = Lot.search([('name', '=', nue), ('product_id', 'in', t.product_variant_ids.ids)], limit=1)
    if not l:
        print('   %-9s %-14s NO SE APLICO' % (cod, nue)); continue
    fis = sum(q.quantity for q in env['stock.quant'].sudo().search([('lot_id', '=', l.id)])
              if q.location_id.usage == 'internal')
    print('   %-9s %-14s ok   existencia=%s (sin cambio)' % (cod, l.name, fis))
