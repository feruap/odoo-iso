"""
Actualizar análisis QC/2026/00032 (id=776) — Hielera chica.

Cambios autorizados por Diana Flores, 2026-09-02:
  - MAVI-11 Ancho: '15.4 cm ± 0.5 cm' → '15-18 cm ± 0.5 cm'
  - MAVI-11 Alto:  '17.0 cm ± 0.5 cm' → '15-18 cm ± 0.5 cm'
  - MAVI-11 Grosor: '2.5 cm ± 0.5 cm' → '2 cm ± 1 cm'
  - MAVI-11 + nueva det: Capacidad de cierre '< 0.5 cm'
  - VAMA-023 (línea y detalle): marcar como N/A (parámetro eliminado)
"""

QCheck  = env['amunet.quality.check']
Line    = env['amunet.quality.test.line']
Detail  = env['amunet.quality.test.line.detail']
SpecConf= env['amunet.quality.parameter.specification.config']
Rel     = env['amunet.quality.parameter.product.rel']
Param   = env['amunet.quality.check.parameter']
SpecBase= env['amunet.quality.check.parameter.specification']

# ── 1. Actualizar criterios de MAVI-11 ────────────────────────────────────────
print("── Actualizando detalles MAVI-11 ──")
Detail.browse(6545).write({'acceptance_criteria': '15-18 cm ± 0.5 cm'})
print("  [6545] Ancho → '15-18 cm ± 0.5 cm'")

Detail.browse(6546).write({'acceptance_criteria': '15-18 cm ± 0.5 cm'})
print("  [6546] Alto → '15-18 cm ± 0.5 cm'")

# Largo [6547] sin cambio
print("  [6547] Largo → sin cambio")

Detail.browse(6548).write({'acceptance_criteria': '2 cm ± 1 cm'})
print("  [6548] Grosor → '2 cm ± 1 cm'")

# ── 2. Agregar detalle Capacidad de cierre a línea MAVI-11 ────────────────────
print("\n── Agregando Capacidad de cierre a línea MAVI-11 [2290] ──")
linea_mavi11 = Line.browse(2290)

# Buscar spec_config de Capacidad de cierre en MAVI-11 (recién creada id=88858)
spec_cc = SpecConf.browse(88858)

# Verificar si ya existe el detalle
ya_det = Detail.search([
    ('line_id', '=', 2290),
    ('name', '=', 'Capacidad de cierre'),
], limit=1)
if not ya_det:
    # Obtener datos del parámetro MAVI-11
    param_mavi11 = Param.search([('code', '=', 'MAVI-11')], limit=1)
    rel_mavi11 = Rel.search([
        ('product_tmpl_id', '=', 988),
        ('parameter_id', '=', param_mavi11.id),
    ], limit=1)
    spec_base_cc = SpecBase.search([
        ('parameter_id', '=', param_mavi11.id),
        ('name', '=', 'Capacidad de cierre'),
    ], limit=1)
    nuevo_det = Detail.create({
        'line_id': 2290,
        'name': 'Capacidad de cierre',
        'specification_id': spec_base_cc.id if spec_base_cc else False,
        'spec_config_id': spec_cc.id if spec_cc else False,
        'evaluation_type': 'numeric_range',
        'acceptance_criteria': '< 0.5 cm',
        'verdict': 'pending',
    })
    print(f"  Detalle Capacidad de cierre creado id={nuevo_det.id}")
else:
    ya_det.write({'acceptance_criteria': '< 0.5 cm'})
    print(f"  Ya existía [{ya_det.id}] — criterio actualizado")

# ── 3. VAMA-023: marcar línea y detalle como N/A ─────────────────────────────
print("\n── Marcando VAMA-023 como N/A ──")
linea_vama = Line.browse(2289)
det_vama   = Detail.browse(6544)
det_vama.write({'verdict': 'not_applicable'})
linea_vama.write({'verdict': 'not_applicable'})
print("  Línea VAMA-023 [2289] → not_applicable")
print("  Detalle [6544] → not_applicable")

env.cr.commit()

# Verificar resultado final
print("\n── Verificación final ──")
c = QCheck.browse(776)
for line in c.test_line_ids:
    print(f"Línea [{line.id}] {line.parameter_id.code} | verdict={line.verdict}")
    for det in line.detail_line_ids:
        print(f"  det [{det.id}] '{det.name}' | criterio: '{det.acceptance_criteria}' | verdict={det.verdict}")

print("\n✓ Análisis QC/2026/00032 actualizado.")
