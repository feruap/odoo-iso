# Finaliza 5 analisis ya firmados por el Responsable Sanitario (Autorizo) y con
# resultado pass, para que pasen a 'Pendiente recepcion almacen' (awaiting_reception)
# y Almacen valide el ingreso. Se ejecuta la logica de finalizacion como Mery
# (uid 61): esta en el grupo Responsable Sanitario y tiene acceso total (la RS
# Patricia no tiene permiso de escribir productos, que la finalizacion actualiza).
# Solicitado por Fernando 2026-07-22.
QC_IDS = [635, 713, 714, 718, 719]
fin = env['res.users'].sudo().browse(61)  # Mery (desarrollo) - RS + acceso total
assert fin.exists() and fin.has_group('amunet_quality.group_quality_sanitary'), 'uid 61 no esta en grupo RS'

for qid in QC_IDS:
    qc = env['amunet.quality.check'].sudo().browse(qid)
    assert qc.exists(), 'no existe QC %s' % qid
    print(qid, qc.name, '| lote', qc.lot_id.name, '| estado antes:', qc.state, '| result:', qc.global_result)
    if qc.state != 'in_progress':
        print('  OMITIDO (no esta in_progress)')
        continue
    qc.with_user(fin)._action_finalize_logic()
    print('  estado despues:', qc.state, '| folio:', qc.analysis_number)

env.cr.commit()
print('LISTO')
