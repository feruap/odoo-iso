"""STCPL04: PL04092601 pasa a CPL04092601, el nombre que le tocaba.

Confirmado por Karla el 28-sep-2026 y autorizado por Mery.

POR QUE ANTES NO SE PUDO Y AHORA SI: cuando se intento el renombrado, el nombre
CPL04092601 estaba ocupado por el lote del 28-sep (27 pz, AMP/IN/00482). Ese lote
se renombro despues a CPL04092603 -- el tercero de septiembre, como pidio Karla --
y con eso CPL04092601 quedo libre para el lote que de verdad le corresponde: el
del 22-sep, de 43 pz.

Este lote se capturo a mano sin la C del prefijo. Su analisis (QC/2026/00506)
esta EN PROCESO, no liberado, asi que el sistema permite corregirlo.

LOS TRES QUE NO SE TOCAN, y no es un olvido: PL04092602, HMC56072601 y
HMC56072602 estan LIBERADOS. El sistema lo prohibe y hace bien -- la identidad de
un lote liberado quedo impresa en su expediente y su certificado --; el camino es
un reanalisis o una desviacion, y eso lo decide Calidad.

Idempotente.
"""

Lot = env['stock.lot'].sudo()
Check = env['amunet.quality.check'].sudo()

VIEJO, NUEVO = 'PL04092601', 'CPL04092601'
prod = env['product.product'].sudo().search([('default_code', '=', 'STCPL04')], limit=1)
assert prod, 'no existe STCPL04'

lote = Lot.search([('name', '=', VIEJO), ('product_id', '=', prod.id)], limit=1)
ya = Lot.search([('name', '=', NUEVO), ('product_id', '=', prod.id)], limit=1)
if ya and not lote:
    print('[ya] %s ya existe (lote %s): nada que renombrar' % (NUEVO, ya.id))
    lote = ya
elif not lote:
    print('[ojo] no existe el lote %s de STCPL04' % VIEJO)
elif ya:
    print('NO SE RENOMBRA: %s ya esta ocupado por el lote %s. Son dos lotes '
          'fisicos distintos y fusionarlos seria peor.' % (NUEVO, ya.id))
    lote = Lot.browse()
else:
    ml = env['stock.move.line'].sudo().search(
        [('lot_id', '=', lote.id), ('state', '=', 'done')], order='date', limit=1)
    recepcion = ml.picking_id.name if ml and ml.picking_id else 'no identificada'
    lote.write({'name': NUEVO})
    lote.message_post(body=(
        'Lote renombrado de %s a %s, confirmado por Karla (Almacen) y autorizado '
        'por Mery el 28-sep-2026.<br/><br/>Se capturo a mano sin la C del prefijo: '
        'a este producto le corresponde CPL04. Es el PRIMER lote de septiembre; el '
        'nombre se libero al pasar el lote del 28-sep a CPL04092603.<br/><br/>'
        'Recepcion de origen: %s'
    ) % (VIEJO, NUEVO, recepcion))
    print('[ok] lote %s renombrado: %s -> %s  (de %s, %g pz)' % (
        lote.id, VIEJO, NUEVO, recepcion, ml.quantity if ml else 0))

# La copia en texto del nombre en su analisis
if lote:
    for qc in Check.search([('lot_id', '=', lote.id)]):
        if (qc.lot_amunet or '') == NUEVO:
            print('    %s ya tenia el nombre correcto' % qc.name); continue
        if qc.state == 'done' or qc.user_authorized_id:
            print('    %s esta finalizado: NO se toca' % qc.name); continue
        try:
            qc.write({'lot_amunet': NUEVO,
                      'change_reason': 'Correccion del prefijo del lote: %s -> %s, '
                                       'confirmada por Almacen (Karla) el '
                                       '28-sep-2026' % (VIEJO, NUEVO)})
            print('    %s: nombre del lote actualizado a %s' % (qc.name, NUEVO))
        except Exception as e:
            print('    %s: no se pudo actualizar el texto -> %s' % (qc.name, str(e)[:110]))

print('\n=== lotes de septiembre de STCPL04 ===')
for l in Lot.search([('product_id', '=', prod.id)], order='create_date'):
    if '0926' not in l.name:
        continue
    ex = sum(env['stock.quant'].sudo().search([
        ('lot_id', '=', l.id), ('location_id.usage', '=', 'internal')]).mapped('quantity'))
    qcs = Check.search([('lot_id', '=', l.id)])
    print('   %-12s %s  %6g pz  %s' % (
        l.name, l.create_date.strftime('%d-%b'), ex,
        ', '.join('%s (%s)' % (c.name, c.state) for c in qcs)))
env.cr.commit()
