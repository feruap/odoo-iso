# -*- coding: utf-8 -*-
# Consolidacion del ANALISIS (QC) del cartucho MPCAC08, para que coincida con el
# inventario ya consolidado (CAC08072601=1680, CAC08072602=0). Habia 2 QC:
#   - 681 (CAC08072601): 980  -> se actualiza a 1680 y se recomputa el muestreo.
#   - 682 (CAC08072602): 700  -> se archiva (lote vacio, duplicado).
# Ambos lotes estan en cuarentena (no liberados). Autorizado por Fernando 2026-07-17.
QC = env['amunet.quality.check'].sudo()
qc_keep = QC.search([('lot_id.name', '=', 'CAC08072601')], limit=1)
qc_drop = QC.search([('lot_id.name', '=', 'CAC08072602')], limit=1)

print('ANTES  -> QC keep (%s): recibida=%s muestra=%s | QC drop (%s): recibida=%s activo=%s' % (
    qc_keep.id, qc_keep.original_qty_received, qc_keep.qty_sampling,
    qc_drop.id, qc_drop.original_qty_received, qc_drop.active))

razon = ('Consolidacion: la recepcion llego con excedente del MISMO lote de '
         'proveedor (DOA-455) y se capturo en 2 lotes por error; se unifico el '
         'inventario en CAC08072601 (1680) y se ajusta el analisis. '
         'Autorizado por Fernando 2026-07-17.')

# 1) QC keep -> 1680 (el muestreo lo ajusta Calidad al analizar)
qc_keep.write({'original_qty_received': 1680.0, 'change_reason': razon})

# 2) Archivar el QC del lote vacio
qc_drop.write({'active': False, 'change_reason': razon})

env.cr.commit()

qc_keep = QC.browse(qc_keep.id)
print('DESPUES-> QC keep (%s): recibida=%s disponible=%s muestra=%s | QC drop archivado=%s' % (
    qc_keep.id, qc_keep.original_qty_received, qc_keep.lot_qty_available,
    qc_keep.qty_sampling, not qc_drop.active))
