# Se agrega a QC/2026/00504 el muestreo que faltaba: Calidad tomo 10 pz y se
# quedo con 5 (destruidas en el analisis), asi que regresa 5 al Almacen Temporal
# de PT. Sirve para ver cuanto queda entregable del lote 0926/01/CAL.
#
# El analisis ya estaba firmado y finalizado, asi que se reabre a 'in_progress'
# para capturar el muestreo en el orden que lo haria Calidad -- qty_to_return es
# readonly una vez confirmado el muestreo-- y se vuelve a correr la disposicion,
# que es la que desecha lo consumido y genera la devolucion.
QC_ID = 931
DIANA = 64

q = env['amunet.quality.check'].browse(QC_ID)
print('== %s  estado=%s  dictamen=%s ==' % (q.name, q.state, q.global_result))
lote = q.lot_id
temporal = env['stock.location'].search([('complete_name','=','APT/Almacén Temporal PT')], limit=1)

def stock(loc):
    return sum(env['stock.quant'].search([
        ('lot_id','=',lote.id), ('location_id','=',loc.id)]).mapped('quantity'))

print('   antes: Temporal PT = %s pz' % stock(temporal))
print()

# El modulo exige 'Razon de cambio' para tocar un analisis que ya salio de
# borrador (traza ISO 13485). Se declara una vez y viaja en los dos writes.
RAZON = ('Registro del muestreo omitido al firmar: Calidad tomo 10 pz y '
         'consumio 5 en el analisis. Se reabre para capturarlo y volver a '
         'correr la disposicion.')
q.sudo().write({'state': 'in_progress', 'sampling_confirmed': False,
                'sampling_move_id': False, 'change_reason': RAZON})
q.sudo().write({'qty_sampling': 10.0, 'qty_analyzed': 5.0, 'qty_to_return': 5.0,
                'change_reason': RAZON})
q.invalidate_recordset()
print('   muestreado=%s  analizado=%s  a devolver=%s  (se quedan %s)'
      % (q.qty_sampling, q.qty_analyzed, q.qty_to_return,
         q.qty_sampling - q.qty_to_return))

q.with_user(DIANA).action_confirm_sampling()
q.invalidate_recordset()
print('   movimiento de muestreo: %s' % (q.sampling_move_id.name or '-'))

msg = q.sudo()._execute_approved_disposition()
q.invalidate_recordset()
print('   disposicion: %s' % msg)
if q.state != 'done':
    q.sudo().write({'state': 'done', 'change_reason': RAZON})
env.cr.commit()

q = env['amunet.quality.check'].browse(QC_ID)
mo = q.amunet_production_id
print()
print('== resultado ==')
print('   analisis %s  estado=%s  folio=%s' % (q.name, q.state, q.analysis_number))
print('   orden    %s  estado=%s  analisis=%s' % (mo.name, mo.state, mo.quality_analysis_status))
print()
print('--- existencia del lote %s ---' % lote.name)
tot = 0
for s in env['stock.quant'].search([('lot_id','=',lote.id)], order='id'):
    if s.quantity:
        interno = s.location_id.usage == 'internal'
        print('   %s %-42s %s' % ('INTERNO' if interno else '       ',
              s.location_id.complete_name[:42], s.quantity))
        if interno:
            tot += s.quantity
print('   TOTAL FISICO: %s' % tot)
print()
print('--- pickings de este analisis ---')
for p in env['stock.picking'].search([('origin','ilike',q.name)], order='id'):
    print('   %-14s %-10s %-26s -> %-26s qty=%s' % (
        p.name, p.state, p.location_id.complete_name[:26],
        p.location_dest_id.complete_name[:26],
        sum(p.move_ids.mapped('product_uom_qty'))))
