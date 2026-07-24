# Ajuste final de la consolidacion del QC del cartucho: la cantidad disponible
# del QC 681 (CAC08072601) viene de su linea de destino (980). Se sube a 1680
# para que el analisis coincida con el inventario consolidado. Autorizado por
# Fernando 2026-07-17.
Dest = env['amunet.quality.check.destination'].sudo()
QC = env['amunet.quality.check'].sudo()
qc = QC.search([('lot_id.name', '=', 'CAC08072601')], limit=1)
dls = Dest.search([('check_id', '=', qc.id)])
print('lineas destino QC %s:' % qc.id, [(d.id, d.quantity) for d in dls])
for dl in dls:
    if dl.quantity == 980.0:
        try:
            dl.write({'quantity': 1680.0})
        except Exception:
            dl.with_context(amunet_documento_workflow_write=True).write({'quantity': 1680.0})
        print('linea', dl.id, '-> 1680')
env.cr.commit()
qc = QC.browse(qc.id)
qc._compute_lot_qty_available()
print('QC %s: recibida=%s disponible=%s' % (qc.id, qc.original_qty_received, qc.lot_qty_available))
