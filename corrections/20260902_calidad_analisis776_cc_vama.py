"""
Completar actualización del análisis QC/2026/00032 (id=776):
- Agregar detalle Capacidad de cierre a línea MAVI-11
- Marcar VAMA-023 como N/A
"""
Line    = env['amunet.quality.test.line']
Detail  = env['amunet.quality.test.line.detail']
SpecConf= env['amunet.quality.parameter.specification.config']
SpecBase= env['amunet.quality.check.parameter.specification']
Param   = env['amunet.quality.check.parameter']

# ── 1. Agregar Capacidad de cierre a línea MAVI-11 [2290] ──
print("── Agregando Capacidad de cierre a MAVI-11 ──")
# El campo correcto es test_line_id (no line_id)
ya_det = Detail.search([
    ('test_line_id', '=', 2290),
    ('name', '=', 'Capacidad de cierre'),
], limit=1)

param_mavi11  = Param.search([('code', '=', 'MAVI-11')], limit=1)
spec_base_cc  = SpecBase.search([
    ('parameter_id', '=', param_mavi11.id),
    ('name', '=', 'Capacidad de cierre'),
], limit=1)
spec_conf_cc  = SpecConf.browse(88858)  # recién creada en el script anterior

if not ya_det:
    # Tomar datos de referencia de otro detalle de la misma línea
    det_ref = Detail.search([('test_line_id', '=', 2290)], limit=1)
    nuevo = Detail.create({
        'test_line_id': 2290,
        'check_id': 776,
        'name': 'Capacidad de cierre',
        'specification_id': spec_base_cc.id if spec_base_cc else False,
        'specification_config_id': spec_conf_cc.id if spec_conf_cc else False,
        'evaluation_type': 'numeric_range',
        'acceptance_criteria': '< 0.5 cm',
        'verdict': 'pending',
        'parameter_id': param_mavi11.id,
    })
    print(f"  Detalle creado id={nuevo.id} | '< 0.5 cm'")
else:
    ya_det.write({'acceptance_criteria': '< 0.5 cm'})
    print(f"  Ya existía [{ya_det.id}] — criterio actualizado")

# ── 2. Marcar VAMA-023 como N/A ──
print("\n── Marcando VAMA-023 como N/A ──")
linea_vama = Line.browse(2289)
det_vama   = Detail.browse(6544)
det_vama.write({'verdict': 'not_applicable'})
linea_vama.write({'verdict': 'not_applicable'})
print("  Línea [2289] VAMA-023 → not_applicable")
print("  Detalle [6544] → not_applicable")

env.cr.commit()

# ── Verificación ──
print("\n── Estado final del análisis ──")
from odoo.addons.amunet_quality.models.amunet_quality_check import AmunetQualityCheck
QCheck = env['amunet.quality.check']
c = QCheck.browse(776)
for line in c.test_line_ids:
    print(f"Línea [{line.id}] {line.parameter_id.code} | verdict={line.verdict}")
    for det in line.detail_line_ids:
        print(f"  [{det.id}] '{det.name}' | criterio: '{det.acceptance_criteria}' | verdict={det.verdict}")
print("\n✓ Listo.")
