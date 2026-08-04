# Archiva los analisis de calidad de anticuerpos (materias primas MPANT*) que
# estan pendientes. Aun NO existe la logica para analizar anticuerpos, y sus
# lotes ya estan en existencias (AMP/Existencias). Se ARCHIVAN (active=False),
# NO se borran, para conservar el registro ISO 13485.
# Autorizado por Fernando 2026-07-29. Idempotente (busca por criterio).
checks = env['amunet.quality.check'].sudo().search([
    ('product_id.default_code', '=like', 'MPANT%'),
    ('state', '!=', 'done'),
    ('active', '=', True),
])
print('Analisis de anticuerpos a archivar:', len(checks))
for c in checks:
    print('  ', c.name, '|', c.product_id.default_code, '|',
          (c.lot_id.name if c.lot_id else '-'), '|', c.state)
checks.write({
    'active': False,
    'change_reason': 'Archivado 2026-07-29: sin logica de analisis de anticuerpos aun; '
                     'lotes MPANT* quedan en existencias (AMP/Existencias). '
                     'Autorizado por Fernando.',
})
env.cr.commit()

rest = env['amunet.quality.check'].sudo().search([
    ('product_id.default_code', '=like', 'MPANT%'),
    ('state', '!=', 'done'),
    ('active', '=', True),
])
print('Pendientes MPANT que quedan activos:', len(rest))
print('LISTO')
