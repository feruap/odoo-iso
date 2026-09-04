"""
Completar actualización análisis 776 — v3 con campos correctos.
"""
Line    = env['amunet.quality.test.line']
Detail  = env['amunet.quality.test.line.detail']
SpecConf= env['amunet.quality.parameter.specification.config']
SpecBase= env['amunet.quality.check.parameter.specification']
Param   = env['amunet.quality.check.parameter']

param_mavi11  = Param.search([('code', '=', 'MAVI-11')], limit=1)
spec_base_cc  = SpecBase.search([
    ('parameter_id', '=', param_mavi11.id),
    ('name', '=', 'Capacidad de cierre'),
], limit=1)
spec_conf_cc  = SpecConf.browse(88858)

# Tomar min_value/max_value de otro detalle de MAVI-11 como referencia de estructura
det_ref = Detail.search([('test_line_id', '=', 2290)], limit=1)
print(f"Detalle referencia: [{det_ref.id}] check_id={det_ref.check_id.id}")

# ── 1. Crear detalle Capacidad de cierre ──────────────────────────────────────
print("\n── Creando Capacidad de cierre en línea MAVI-11 ──")
ya_det = Detail.search([
    ('test_line_id', '=', 2290),
    ('name', '=', 'Capacidad de cierre'),
], limit=1)
if not ya_det:
    nuevo = Detail.create({
        'test_line_id':         2290,
        'check_id':             776,
        'name':                 'Capacidad de cierre',
        'specification_id':     spec_base_cc.id if spec_base_cc else False,
        'specification_config_id': spec_conf_cc.id if spec_conf_cc else False,
        'evaluation_type':      'numeric_range',
        'acceptance_criteria':  '< 0.5 cm',
        'max_value':            0.5,
        'verdict':              'pending',
    })
    print(f"  Detalle creado id={nuevo.id}")
else:
    ya_det.write({'acceptance_criteria': '< 0.5 cm', 'max_value': 0.5})
    print(f"  Ya existía [{ya_det.id}] — actualizado")

# ── 2. Marcar VAMA-023 como N/A ───────────────────────────────────────────────
print("\n── Marcando VAMA-023 como N/A ──")
Detail.browse(6544).write({'verdict': 'not_applicable'})
Line.browse(2289).write({'verdict': 'not_applicable'})
print("  VAMA-023 → not_applicable")

env.cr.commit()

# Verificación final
print("\n── Estado final ──")
QCheck = env['amunet.quality.check']
c = QCheck.browse(776)
for line in c.test_line_ids:
    print(f"Línea [{line.id}] {line.parameter_id.code} | verdict={line.verdict}")
    for det in line.detail_line_ids:
        print(f"  [{det.id}] '{det.name}' | criterio: '{det.acceptance_criteria}' | verdict={det.verdict}")
print("\n✓ Listo.")
