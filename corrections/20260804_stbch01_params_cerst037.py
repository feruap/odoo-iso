"""
Limpia y configura los parámetros de QC de STBCH01
(Vial solución corrimiento Sangre/Suero/Plasma con Chems, ST-037)
según el CERST-037.

Valores del CERST-037:
  MAVI-09 — Liberación: 1–30 s   (estándar)
  MAVI-09 — Migración:  30–180 s (estándar)
  MAVI-07 — Muestra negativa: "#5 y/o #1-4 (patrón PRB-01)"
  MAVI-07 — Muestra positiva: "#1-4 y/o #5 (patrón PRB-01)"
  MAVI-13 — Partículas en solución: Sin partículas suspendidas
  MGA 0701 — pH: 7.4 ± 0.5 (6.9–7.9)
  MGA 0981 — Variación de volumen: ≥ 2.5 mL

IDs de rels:
  MAVI-07=89, MAVI-09=87, MAVI-13=83, MGA 0701=85, MGA 0981=81

Canonical spec IDs (únicos con FK en tld):
  78132 (MAVI-07→Muestra neg), 78130 (Lib), 78131 (Mig),
  78128 (MAVI-13), 78129 (MGA 0701), 78127 (MGA 0981)

Idempotente — seguro de correr más de una vez.
Correr UNA VEZ después del deploy a producción.
"""

# ── 1. Actualizar specs canónicas ─────────────────────────────────────────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id    = 146,
        specification_name  = 'Liberación de conjugado',
        evaluation_type     = 'numeric_range',
        min_value           = 1,
        max_value           = 30,
        acceptance_criteria = '1 a 30 segundos',
        sequence            = 10,
        write_date          = NOW()
    WHERE id = 78130
""")
print("MAVI-09 Liberación (id=78130): → 1–30 s")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id    = 126,
        specification_name  = 'Migración de conjugado',
        evaluation_type     = 'numeric_range',
        min_value           = 30,
        max_value           = 180,
        acceptance_criteria = '30 a 180 segundos',
        sequence            = 20,
        write_date          = NOW()
    WHERE id = 78131
""")
print("MAVI-09 Migración (id=78131): → 30–180 s")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id    = 628,
        specification_name  = 'Muestra negativa',
        evaluation_type     = 'mavi_07_ternary',
        min_value           = 0,
        max_value           = 0,
        acceptance_criteria = '#5 y/o #1-4 (patrón PRB-01)',
        sequence            = 20,
        write_date          = NOW()
    WHERE id = 78132
""")
print("MAVI-07 Muestra negativa (id=78132): actualizado")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id    = 74,
        specification_name  = 'Partículas en solución',
        evaluation_type     = 'binary_selection',
        min_value           = 0,
        max_value           = 0,
        acceptance_criteria = 'Sin partículas suspendidas',
        sequence            = 10,
        write_date          = NOW()
    WHERE id = 78128
""")
print("MAVI-13 Partículas (id=78128): Sin partículas suspendidas")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id    = 87,
        specification_name  = 'pH de solución',
        evaluation_type     = 'numeric_range',
        min_value           = 6.9,
        max_value           = 7.9,
        acceptance_criteria = '7.4 ± 0.5',
        sequence            = 10,
        write_date          = NOW()
    WHERE id = 78129
""")
print("MGA 0701 pH (id=78129): → 6.9–7.9")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id    = 86,
        specification_name  = 'Variación de volumen',
        evaluation_type     = 'numeric_range',
        min_value           = 2.5,
        max_value           = 999999,
        acceptance_criteria = '≥ 2.5 mL',
        sequence            = 10,
        write_date          = NOW()
    WHERE id = 78127
""")
print("MGA 0981 Volumen (id=78127): → ≥ 2.5 mL")

# ── 2. Insertar "Muestra positiva" para MAVI-07 (rel_id=89) ──────────────────
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id, specification_id, specification_name,
       evaluation_type, min_value, max_value, acceptance_criteria, sequence,
       create_date, write_date, create_uid, write_uid)
    VALUES (89, 629, 'Muestra positiva', 'mavi_07_ternary', 0, 0,
            '#1-4 y/o #5 (patrón PRB-01)', 10, NOW(), NOW(), 1, 1)
    ON CONFLICT DO NOTHING
""")
print("MAVI-07 Muestra positiva: insertada (rel_id=89)")

# ── 3. Eliminar specs duplicadas ──────────────────────────────────────────────
DELETE_MAVI07 = [
    74823,75379,75380,75505,75506,75645,75646,75861,75862,76184,76185,
    76254,76255,76433,76434,76649,76650,76865,76866,77081,77082,77607,77608,77916,77917,
]
DELETE_MAVI09 = [
    141,142,75643,75644,75859,75860,76182,76183,76252,76253,76431,76432,
    76647,76648,76863,76864,77079,77080,77605,77606,77914,77915,
]
DELETE_MAVI13 = [136,75641,75857,76073,76429,76645,76861,77077,77603,77912]
DELETE_MGA0701 = [73056,75504,75642,75858,76181,76251,76430,76646,76862,77078,77604,77913]
DELETE_MGA0981 = [73057,75640,75856,76180,76250,76428,76644,76860,77076,77602,77911]

for label, ids in [
    ('MAVI-07',  DELETE_MAVI07),
    ('MAVI-09',  DELETE_MAVI09),
    ('MAVI-13',  DELETE_MAVI13),
    ('MGA 0701', DELETE_MGA0701),
    ('MGA 0981', DELETE_MGA0981),
]:
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE id = ANY(%s)",
        (ids,)
    )
    print(f"{label}: {env.cr.rowcount} specs duplicadas eliminadas")

env.cr.commit()
print("\nLISTO — STBCH01 (ST-037) configurado con 7 specs limpias del CERST-037.")
print("Verificar en staging: https://stagingfc.amunet.com.mx/odoo/quality-checks")
