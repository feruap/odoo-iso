"""
CORRECCIÓN RAÍZ — 3 problemas de configuración de producto (producción)
========================================================================

1. SPHMC04 (Hoja Maestra Albúmina cualitativa) — MAVI-09
   Tiene 5 specs; solo debe tener 2 (igual que SPHMC03/05).
   Deactivar: Liberación de conjugado (21635), Migración de conjugado (21636),
              Tiempo de migración en 4 cm de membrana. (78455)
   Conservar: Tiempo de liberación (21638), Tiempo de migración (21637)
   También limpiar análisis 547 (borrador) de esas 3 rows extras.

2. DMTOR02 (ToRCH IgG/IgM) — MAVI-13 no debería existir en PT
   Deactivar: cfg_ids 84950, 84951, 84952, 84953
   (Agregados por script __system__ el 10-ago; análisis aprobado 893 no los tiene)

3. DLLFS01 (LabFast Salmonella spp) — MAVI-13 no debería existir en PT
   Deactivar: cfg_ids 88594, 88595, 88596, 88597
   (Agregados por script __system__ el 24-ago)

Solicitado por: Diana Flores — Control de Calidad, 2026-09-23
"""

Config = env['amunet.quality.parameter.specification.config']
Detail = env['amunet.quality.test.line.detail']

# ─────────────────────────────────────────────
# 1. SPHMC04 — desactivar 3 configs sobrantes
# ─────────────────────────────────────────────
cfg_sphmc04_quitar = [21635, 21636, 78455]
cfgs = Config.browse(cfg_sphmc04_quitar)
for c in cfgs:
    print(f"  Desactivando SPHMC04 MAVI-09 cfg {c.id}: {c.specification_name.strip()}")
cfgs.write({'active': False})

# Limpiar análisis 547 (borrador) — eliminar las 3 rows correspondientes
details_quitar = [3201, 3202, 3205]
details = Detail.browse(details_quitar).filtered(lambda d: d.exists())
print(f"\n  Eliminando {len(details)} rows de análisis 547 (borrador):")
for d in details:
    print(f"    detail {d.id}: {d.name}")
details.unlink()

# Verificar lo que queda en SPHMC04 MAVI-09
print("\n  SPHMC04 MAVI-09 — specs que quedan:")
cfgs_ok = Config.search([
    ('product_parameter_rel_id.product_tmpl_id.default_code', '=', 'SPHMC04'),
    ('product_parameter_rel_id.parameter_code', '=', 'MAVI-09'),
    ('active', '=', True),
])
for c in cfgs_ok:
    print(f"    cfg {c.id}: {c.specification_name.strip()} ({c.evaluation_type}) {c.min_value}-{c.max_value}")

# ─────────────────────────────────────────────
# 2. DMTOR02 — eliminar MAVI-13
# ─────────────────────────────────────────────
cfg_dmtor02 = [84950, 84951, 84952, 84953]
cfgs2 = Config.browse(cfg_dmtor02)
print(f"\n  Desactivando DMTOR02 MAVI-13 ({len(cfgs2)} configs):")
for c in cfgs2:
    print(f"    cfg {c.id}: {c.specification_name.strip()}")
cfgs2.write({'active': False})

# ─────────────────────────────────────────────
# 3. DLLFS01 — eliminar MAVI-13
# ─────────────────────────────────────────────
cfg_dllfs01 = [88594, 88595, 88596, 88597]
cfgs3 = Config.browse(cfg_dllfs01)
print(f"\n  Desactivando DLLFS01 MAVI-13 ({len(cfgs3)} configs):")
for c in cfgs3:
    print(f"    cfg {c.id}: {c.specification_name.strip()}")
cfgs3.write({'active': False})

env.cr.commit()

# ─────────────────────────────────────────────
# Verificación final
# ─────────────────────────────────────────────
print("\n─── Verificación ─────────────────────────────")

# MAVI-13 en PT activos — debe ser cero
mavi13_pt = Config.search([
    ('product_parameter_rel_id.product_tmpl_id.default_code', 'in', ['DLLFS01', 'DMTOR02']),
    ('product_parameter_rel_id.parameter_code', '=', 'MAVI-13'),
    ('active', '=', True),
])
print(f"MAVI-13 activos en DLLFS01/DMTOR02: {len(mavi13_pt)} (debe ser 0)")

# SPHMC04 análisis 547 detalles restantes
details_restantes = Detail.search([('test_line_id.check_id', '=', 547),
                                    ('test_line_id.code', '=', 'MAVI-09')])
print(f"SPHMC04 análisis 547 MAVI-09 rows: {len(details_restantes)} (debe ser 2)")
for d in details_restantes:
    print(f"  {d.name}: {d.evaluation_type} {d.min_value}-{d.max_value}")

print("\n✓ Listo.")
