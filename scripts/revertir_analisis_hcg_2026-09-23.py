# 0926/01/HCG: el analisis se solicito con la cantidad equivocada (PARCIAL de
# 260 pz sobre un lote de 1100) y ademas el muestreo se confirmo DOS veces, asi
# que Calidad tiene 64 pz en su ubicacion en vez de 32.
#
# Mery confirma que el analisis NO se ha realizado. Se regresa la orden a
# 'Pendiente de Solicitar' para pedirlo de nuevo con la cantidad correcta.
#
# Se revierte exactamente lo que escribe el asistente (amunet_analysis_wizard):
# qty_producing, quality_analysis_status y amunet_pt_qty_solicitada, mas el
# analisis que crea. El analisis NO tiene estado de cancelado, por eso se
# archiva en vez de borrarse: el registro se conserva para ISO.
MO = env['mrp.production']
QC = env['amunet.quality.check']
NOTA = ('Analisis archivado el 23-sep-2026 a peticion de Mery (Desarrollo): se '
        'solicito con la cantidad equivocada (parcial de 260 pz sobre un lote '
        'de 1100) y el muestreo se confirmo dos veces (APT/IN/00066 y '
        'APT/IN/00070, 32 pz cada uno). El analisis no se habia realizado. Se '
        'regresa la orden a Pendiente de Solicitar para pedirlo de nuevo.')

mo = MO.search([('name', '=', '0926/01/HCG')], limit=1)
assert mo, 'No existe la orden'
chk = QC.search([('name', '=', 'QC/2026/00480')], limit=1)
assert chk, 'No existe el analisis'
assert chk.state not in ('done',), 'El analisis ya esta finalizado, no se toca'

# --- 1. devolver a Almacen Temporal PT lo que se llevo el muestreo ----------
lot = mo.lot_producing_ids[:1]
origen = env['stock.location'].search([('complete_name', 'like', 'APT/Control de calidad')], limit=1)
destino = env['stock.location'].search([('complete_name', 'like', 'APT/%Temporal%')], limit=1)
assert origen and destino, 'No se encontraron las ubicaciones'
q = env['stock.quant'].search([('lot_id', '=', lot.id), ('location_id', '=', origen.id)])
pz = sum(q.mapped('quantity'))
if pz > 0:
    mv = env['stock.move'].create({
        'product_id': lot.product_id.id, 'product_uom': lot.product_id.uom_id.id,
        'product_uom_qty': pz, 'location_id': origen.id, 'location_dest_id': destino.id,
        'origin': 'Reverso del muestreo de %s (analisis archivado)' % chk.name,
    })
    mv._action_confirm()
    mv.move_line_ids.unlink()
    env['stock.move.line'].create({
        'move_id': mv.id, 'product_id': lot.product_id.id, 'lot_id': lot.id,
        'quantity': pz, 'product_uom_id': lot.product_id.uom_id.id,
        'location_id': origen.id, 'location_dest_id': destino.id,
    })
    mv.picked = True
    mv._action_done()
    print('  devueltas %s pz de %s a %s' % (pz, origen.name, destino.name))
else:
    print('  no habia piezas en Control de calidad')

# --- 2. archivar el analisis ------------------------------------------------
# El propio analisis exige 'Razon de cambio' para modificarlo fuera de
# borrador: es un control ISO y se respeta, no se rodea.
chk.message_post(body=NOTA)
chk.write({'change_reason': NOTA, 'active': False})
print('  archivado %s (estado que traia: %s)' % (chk.name, chk.state))

# --- 3. regresar la orden a Pendiente de Solicitar --------------------------
mo.message_post(body=NOTA)
mo.qty_producing = 1100.0
mo.write({'quality_analysis_status': 'to_request', 'amunet_pt_qty_solicitada': 0.0})
env.cr.commit()

mo.invalidate_recordset()
print('\n--- como queda 0926/01/HCG ---')
print('  analisis           : %s' % mo.quality_analysis_status)
print('  solicitada         : %s   qty_producing: %s' % (mo.amunet_pt_qty_solicitada, mo.qty_producing))
print('  sin analizar       : %s' % mo.amunet_pt_qty_sin_analizar)
print('  analisis activos   : %s' % mo.amunet_qc_check_count)
print('  puede pedir analisis: %s' % mo.amunet_puede_pedir_analisis)
for qq in env['stock.quant'].search([('lot_id', '=', lot.id), ('quantity', '!=', 0)]):
    print('  %-40s %s' % (qq.location_id.complete_name, qq.quantity))
