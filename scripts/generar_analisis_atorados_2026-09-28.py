# Genera los analisis de los cinco lotes que llevaban entre 3 y 37 dias parados
# en Control de calidad SIN analisis, porque apply_quality_points no creaba nada
# cuando el producto no aparecia en ningun punto de calidad (corregido hoy en
# amunet_quality 19.0.3.63.0, PR #128). Autorizado por Mery el 28-sep-2026.
#
# El arreglo cubre las recepciones FUTURAS; estos cinco ya habian pasado, asi
# que se les crea el analisis a mano con el MISMO mecanismo: los parametros se
# cargan del producto con _load_product_parameters, igual que hace ahora el
# codigo. No se inventan parametros ni se tocan los del catalogo.
#
# NO entran aqui los dos combos (D000-4055 y D000-8053-A): tienen
# qc_required=False, o sea NO requieren analisis. Estan en cuarentena por otra
# razon -salieron de una conversion de combos y no tienen ruta de salida
# definida- y eso lo resuelve Almacen con un traslado, no Calidad con un
# analisis.
LOTES = [
    ('STCPL04', 'PL04092601'),
    ('STCPL04', 'PL04092602'),
    ('STCPL14', 'PL14092601'),
    ('SPHMC56', 'HMC56072602'),
    ('STGEL02', 'GEL02082601'),
]

QC = env['amunet.quality.check'].sudo()
Lot = env['stock.lot'].sudo()
creados = []
print('%-10s %-16s %-16s %-7s %s' % ('PRODUCTO', 'LOTE', 'ANALISIS', 'LINEAS', 'NOTA'))
for cod, nombre_lote in LOTES:
    pr = env['product.product'].sudo().search([('default_code', '=', cod)], limit=1)
    assert pr, 'no existe el producto %s' % cod
    lote = Lot.search([('name', '=', nombre_lote), ('product_id', '=', pr.id)], limit=1)
    assert lote, 'no existe el lote %s de %s' % (nombre_lote, cod)
    # Guarda: si ya tiene analisis, no se duplica.
    ya = QC.search([('lot_id', '=', lote.id)])
    if ya:
        print('%-10s %-16s %-16s %-7s ya tenia, no se toca' % (cod, nombre_lote, ya[0].name, '-'))
        continue
    # Guarda: solo para productos que de verdad lo requieren.
    assert pr.product_tmpl_id.qc_required, \
        '%s tiene qc_required apagado: no se le genera analisis' % cod
    # De donde vino, para dejarlo ligado a su recepcion.
    ml = env['stock.move.line'].sudo().search(
        [('lot_id', '=', lote.id), ('state', '=', 'done')], order='date', limit=1)
    vals = {
        'product_id': pr.id,
        'lot_id': lote.id,
        'lot_amunet': lote.name,
        'sampling_uom_id': pr.uom_id.id,
    }
    if ml and ml.picking_id:
        vals['picking_id'] = ml.picking_id.id
        if ml.picking_id.partner_id:
            vals['partner_id'] = ml.picking_id.partner_id.id
    if getattr(lote, 'expiration_date', False):
        vals['expiration_date'] = lote.expiration_date
    if getattr(lote, 'manufacturing_date', False):
        vals['manufacturing_date'] = lote.manufacturing_date
    qc = QC.create(vals)
    qc._load_product_parameters()
    nota = ''
    if not qc.test_line_ids:
        nota = 'SIN PARAMETROS: Calidad debe configurarlos'
        qc.message_post(body=(
            'Analisis generado <b>sin parametros</b>: el producto %s no tiene '
            'parametros de calidad configurados ni aparece en ningun punto de '
            'control.<br/><br/>El material lleva dias en cuarentena esperando. '
            'Configura los parametros del producto y vuelve a abrir el analisis.'
        ) % pr.display_name)
    qc.message_post(body=(
        'Analisis generado por Desarrollo, autorizado por Mery.<br/><br/>'
        'Este lote llevaba parado en Control de calidad sin analisis porque '
        '%s no aparecia en ningun punto de calidad, y hasta hoy el sistema no '
        'creaba el analisis en ese caso. Corregido en amunet_quality '
        '19.0.3.63.0: ahora manda la bandera del producto, no el punto.<br/><br/>'
        'Recepcion de origen: %s'
    ) % (cod, (ml.picking_id.name if ml and ml.picking_id else 'no identificada')))
    creados.append((cod, nombre_lote, qc))
    print('%-10s %-16s %-16s %-7s %s' % (cod, nombre_lote, qc.name, len(qc.test_line_ids), nota))

env.cr.commit()
print()
print('=== comprobacion: queda material en cuarentena sin analisis? ===')
qc_locs = env['stock.location'].sudo().search([('complete_name', 'ilike', 'Control de calidad')])
falta = []
for q in env['stock.quant'].sudo().search([('location_id', 'in', qc_locs.ids), ('quantity', '>', 0)]):
    if q.lot_id and QC.search_count([('lot_id', '=', q.lot_id.id)]):
        continue
    falta.append('%s %s (%s pz, qc_required=%s)' % (
        q.product_id.default_code, q.lot_id.name if q.lot_id else '(sin lote)',
        q.quantity, q.product_id.product_tmpl_id.qc_required))
for f in falta:
    print('   %s' % f)
print('   quedan %s sin analisis (los que tengan qc_required=False no lo necesitan)' % len(falta))
