# Archiva (active=False, NO borra) los analisis de calidad NO finalizados cuyo lote
# NO tiene existencia interna (lotes fantasma del arranque del sistema 2026-03-12 +
# unos recientes sin stock). Se conservan los que tienen stock real (en cuarentena/
# en proceso). Registros regulatorios ISO: se archivan con change_reason, no se borran.
# Autorizado por Fernando 2026-07-28.
env.cr.execute("""
    SELECT qc.id FROM amunet_quality_check qc
    WHERE qc.state != 'done'
      AND NOT EXISTS (
        SELECT 1 FROM stock_quant sq JOIN stock_location sl ON sl.id=sq.location_id
        WHERE sq.lot_id = qc.lot_id AND sl.usage='internal' AND sq.quantity <> 0
      )
""")
ids = [r[0] for r in env.cr.fetchall()]
print('Analisis a archivar (sin existencia):', len(ids))
recs = env['amunet.quality.check'].sudo().browse(ids)
recs.write({
    'active': False,
    'change_reason': 'Archivado 2026-07-28: analisis de lote SIN existencia '
                     '(fantasma del arranque del sistema, no es inventario real). '
                     'Autorizado por Fernando.',
})
env.cr.commit()

# verificacion
env.cr.execute("SELECT state, count(*) FROM amunet_quality_check WHERE state!='done' AND active GROUP BY state ORDER BY count DESC")
print('Pendientes que QUEDAN activos (con existencia):', env.cr.fetchall())
env.cr.execute("SELECT count(*) FROM amunet_quality_check WHERE active=false AND state!='done'")
print('Total archivados no-finalizados:', env.cr.fetchone()[0])
print('LISTO')
