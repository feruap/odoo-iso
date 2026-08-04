# Archiva el analisis de calidad fantasma de la centrifuga EQCBV01 (QC/2026/00075).
# Un equipo NO se analiza como reactivo (se calibra); artefacto del arranque 2026-03-12.
# Se archiva (active=False), NO se borra (ISO). Autorizado por Fernando 2026-07-29.
qc = env['amunet.quality.check'].sudo().search([
    ('product_id.default_code', '=', 'EQCBV01'),
    ('state', '!=', 'done'),
    ('active', '=', True),
])
print('Analisis de centrifuga a archivar:', len(qc), qc.mapped('name'))
qc.write({
    'active': False,
    'change_reason': 'Archivado 2026-07-29: analisis fantasma sobre un EQUIPO (centrifuga); '
                     'los equipos se controlan por calibracion, no por analisis de calidad. '
                     'Artefacto del arranque. Autorizado por Fernando.',
})
env.cr.commit()
print('LISTO')
