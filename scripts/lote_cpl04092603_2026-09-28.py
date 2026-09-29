"""STCPL04: el lote de AMP/IN/00482 pasa a CPL04092603.

Pedido por Karla el 28-sep-2026 y autorizado por Mery.

LO QUE REPORTO KARLA: "AMP/IN/00482 genero CPL04092601 pero ese nombre ya esta
ocupado"; deberia ser CPL04092603.

LO QUE ENCONTRAMOS AL REVISAR, que es distinto: no habia dos lotes con el mismo
nombre. Los lotes de septiembre de este producto son:

    PL04092601    22-sep   AMP/IN/00473   <-- sin la C del prefijo
    PL04092602    24-sep   AMP/IN/00480   <-- sin la C del prefijo
    CPL04092601   28-sep   AMP/IN/00482   <-- este si con la C

La secuencia del producto esta bien configurada (CPL04%(month)s%(y)s, padding 2).
Los dos primeros se capturaron A MANO y les falto la C, asi que el numerador no
los conto como lotes de septiembre con ese prefijo y empezo otra vez en 01.

De ahi que Karla los vea como CPL04092601 y CPL04092602 -- que es lo que dicen sus
etiquetas -- mientras el sistema tiene PL04092601 y PL04092602.

QUE HACE ESTE SCRIPT: solo lo que se pidio. El lote de hoy pasa a CPL04092603,
que es el tercero de septiembre, y la secuencia avanza para que el siguiente sea
el 04. Tambien se alinea la copia en texto del nombre en su analisis, que esta en
borrador.

QUE NO TOCA, y por que: los dos lotes mal escritos se quedan como estan.
El analisis de PL04092602 (QC/2026/00507) esta CERRADO, y lo firmado y cerrado no
se toca. Ademas habria que confirmar con Karla que dicen las etiquetas fisicas
antes de renombrar un lote que ya circula. Queda reportado a ella.

Idempotente.
"""

Lot = env['stock.lot'].sudo()
Check = env['amunet.quality.check'].sudo()

VIEJO, NUEVO = 'CPL04092601', 'CPL04092603'
prod = env['product.product'].sudo().search([('default_code', '=', 'STCPL04')], limit=1)
assert prod, 'no existe STCPL04'

ya = Lot.search([('name', '=', NUEVO), ('product_id', '=', prod.id)], limit=1)
lote = Lot.search([('name', '=', VIEJO), ('product_id', '=', prod.id)], limit=1)
if ya:
    print('[ya] %s ya existe (lote %s): nada que renombrar' % (NUEVO, ya.id))
    lote = ya
elif not lote:
    print('[ojo] no existe ningun lote %s de STCPL04 en esta base' % VIEJO)
    lote = Lot.browse()
else:
    # De que recepcion viene, para dejarlo dicho
    ml = env['stock.move.line'].sudo().search(
        [('lot_id', '=', lote.id), ('state', '=', 'done')], order='date', limit=1)
    recepcion = ml.picking_id.name if ml and ml.picking_id else 'no identificada'
    lote.write({'name': NUEVO})
    lote.message_post(body=(
        'Lote renombrado de %s a %s por indicacion de Karla (Almacen) y '
        'autorizacion de Mery, 28-sep-2026.<br/><br/>Es el TERCER lote de '
        'septiembre de este producto. Los dos anteriores (%s) se capturaron a '
        'mano sin la C del prefijo, asi que el numerador no los conto y volvio a '
        'empezar en 01.<br/><br/>Recepcion de origen: %s'
    ) % (VIEJO, NUEVO, 'PL04092601 y PL04092602', recepcion))
    print('[ok] lote %s renombrado: %s -> %s  (de %s)' % (lote.id, VIEJO, NUEVO, recepcion))

# La copia en texto del nombre, en su analisis (solo si esta en borrador)
if lote:
    for qc in Check.search([('lot_id', '=', lote.id)]):
        if (qc.lot_amunet or '') == NUEVO:
            print('    %s ya tenia el nombre correcto' % qc.name)
            continue
        if qc.state != 'draft':
            print('    %s esta en %s: NO se toca (solo se ajusta en borrador)' % (
                qc.name, qc.state))
            continue
        qc.write({'lot_amunet': NUEVO})
        print('    %s: nombre del lote actualizado a %s' % (qc.name, NUEVO))

# La secuencia, para que el siguiente sea el 04
seq = prod.product_tmpl_id.lot_sequence_id
if seq:
    usados = Lot.search([('product_id', '=', prod.id),
                         ('name', 'like', 'CPL040926%')]).mapped('name')
    consecutivos = []
    for n in usados:
        cola = n.replace('CPL040926', '')
        if cola.isdigit():
            consecutivos.append(int(cola))
    siguiente = (max(consecutivos) + 1) if consecutivos else 1
    if seq.number_next_actual != siguiente:
        antes = seq.number_next_actual
        seq.write({'number_next_actual': siguiente})
        print('[ok] secuencia %s: siguiente %s -> %s (lotes usados: %s)' % (
            seq.name, antes, siguiente, sorted(usados)))
    else:
        print('[ya] la secuencia ya apunta al %s' % siguiente)

print('\n=== lotes de septiembre de STCPL04 ===')
for l in Lot.search([('product_id', '=', prod.id)], order='create_date'):
    if '0926' not in l.name:
        continue
    ml = env['stock.move.line'].sudo().search(
        [('lot_id', '=', l.id), ('state', '=', 'done')], order='date', limit=1)
    print('   %-12s %s  %s' % (l.name, l.create_date.strftime('%d-%b'),
                               ml.picking_id.name if ml and ml.picking_id else ''))

env.cr.commit()
