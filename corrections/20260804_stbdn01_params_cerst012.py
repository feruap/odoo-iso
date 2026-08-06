"""
Limpia y configura los parámetros de QC de STBDN01 (AC+PBS, ST-012)
según el CERST-012.

Valores confirmados (Diana Flores, 2026-07-26):
  MAVI-09 — Liberación: 1–30 s / Migración: 30–240 s
             (caso especial: buffer para Dengue combo, que migra más lento)
  MAVI-07 — Muestra negativa: "#5 y/o #1-4 (patrón PRB-01)"
             Muestra positiva: "#1-4 y/o #5 (patrón PRB-01)"
  MAVI-13 — Partículas en solución: Sin partículas suspendidas
  MGA 0701 — pH: 6.9–7.9 (7.4 ± 0.5)
  MGA 0981 — Volumen: ≥ 2.5 mL

IDs de rels (ya existentes en staging):
  MAVI-07=260, MAVI-09=259, MAVI-13=257, MGA 0701=258, MGA 0981=256

Canonical spec IDs (únicos con FK en amunet_quality_test_line_detail):
  78151 (Liberación), 78152 (Migración), 78153 (Interpretación→Muestra neg),
  78149 (Partículas), 78150 (pH), 78148 (Volumen)

Idempotente — seguro de correr más de una vez.
Correr UNA VEZ después del deploy a producción.
"""

# ── Canonical spec IDs (los que tienen TLD refs; se actualizan en lugar de borrar) ──
CANON_MAVI09_LIB  = 78151
CANON_MAVI09_MIG  = 78152
CANON_MAVI07      = 78153   # se convierte en "Muestra negativa"
CANON_MAVI13      = 78149
CANON_MGA0701     = 78150
CANON_MGA0981     = 78148

# ── Todos los IDs de specs duplicadas a eliminar ──────────────────────────────
DELETE_MAVI09 = [
    624,625,75664,75665,75880,75881,76200,76201,76270,76271,
    76452,76453,76668,76669,76884,76885,77100,77101,77626,77627,77935,77936,
]
DELETE_MAVI07 = [
    74829,75386,75387,75514,75515,75666,75667,75882,75883,76202,76203,76272,
    76273,76454,76455,76670,76671,76886,76887,77102,77103,77628,77629,77937,77938,
]
DELETE_MAVI13 = [622,75662,75878,76094,76450,76666,76882,77098,77624,77933]
DELETE_MGA0701 = [73060,75513,75663,75879,76199,76269,76451,76667,76883,77099,77625,77934]
DELETE_MGA0981 = [73061,75661,75877,76198,76268,76449,76665,76881,77097,77623,77932]

# ── 1. Actualizar specs canónicas con valores del CERST-012 ──────────────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id     = 146,
        specification_name   = 'Liberación de conjugado',
        evaluation_type      = 'numeric_range',
        min_value            = 1,
        max_value            = 30,
        acceptance_criteria  = '1 a 30 segundos',
        sequence             = 10,
        write_date           = NOW()
    WHERE id = %s
""", (CANON_MAVI09_LIB,))
print(f"MAVI-09 Liberación (id={CANON_MAVI09_LIB}): → 1–30 s")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id     = 126,
        specification_name   = 'Migración de conjugado',
        evaluation_type      = 'numeric_range',
        min_value            = 30,
        max_value            = 240,
        acceptance_criteria  = '30 a 240 segundos',
        sequence             = 20,
        write_date           = NOW()
    WHERE id = %s
""", (CANON_MAVI09_MIG,))
print(f"MAVI-09 Migración (id={CANON_MAVI09_MIG}): → 30–240 s")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id     = 628,
        specification_name   = 'Muestra negativa',
        evaluation_type      = 'mavi_07_ternary',
        min_value            = 0,
        max_value            = 0,
        acceptance_criteria  = '#5 y/o #1-4 (patrón PRB-01)',
        sequence             = 20,
        write_date           = NOW()
    WHERE id = %s
""", (CANON_MAVI07,))
print(f"MAVI-07 Muestra negativa (id={CANON_MAVI07}): actualizado")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id     = 74,
        specification_name   = 'Partículas en solución',
        evaluation_type      = 'binary_selection',
        min_value            = 0,
        max_value            = 0,
        acceptance_criteria  = 'Sin partículas suspendidas',
        sequence             = 10,
        write_date           = NOW()
    WHERE id = %s
""", (CANON_MAVI13,))
print(f"MAVI-13 Partículas (id={CANON_MAVI13}): → Sin partículas suspendidas")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id     = 87,
        specification_name   = 'pH de solución',
        evaluation_type      = 'numeric_range',
        min_value            = 6.9,
        max_value            = 7.9,
        acceptance_criteria  = '7.4 ± 0.5',
        sequence             = 10,
        write_date           = NOW()
    WHERE id = %s
""", (CANON_MGA0701,))
print(f"MGA 0701 pH (id={CANON_MGA0701}): → 6.9–7.9")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id     = 86,
        specification_name   = 'Volumen',
        evaluation_type      = 'numeric_range',
        min_value            = 2.5,
        max_value            = 999999,
        acceptance_criteria  = '≥ 2.5 mL',
        sequence             = 10,
        write_date           = NOW()
    WHERE id = %s
""", (CANON_MGA0981,))
print(f"MGA 0981 Volumen (id={CANON_MGA0981}): → ≥2.5 mL")

# ── 2. Insertar "Muestra positiva" para MAVI-07 (rel_id=260) ─────────────────
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id, specification_id, specification_name,
       evaluation_type, min_value, max_value, acceptance_criteria, sequence,
       create_date, write_date, create_uid, write_uid)
    VALUES (260, 629, 'Muestra positiva', 'mavi_07_ternary', 0, 0,
            '#1-4 y/o #5 (patrón PRB-01)', 10, NOW(), NOW(), 1, 1)
    ON CONFLICT DO NOTHING
""")
print(f"MAVI-07 Muestra positiva: insertada")

# ── 3. Eliminar specs duplicadas (sin FK refs en tld) ────────────────────────
for label, ids in [
    ('MAVI-09', DELETE_MAVI09),
    ('MAVI-07', DELETE_MAVI07),
    ('MAVI-13', DELETE_MAVI13),
    ('MGA 0701', DELETE_MGA0701),
    ('MGA 0981', DELETE_MGA0981),
]:
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE id = ANY(%s)",
        (ids,)
    )
    print(f"{label}: {env.cr.rowcount} specs duplicadas eliminadas")

env.cr.commit()
print("\nLISTO — STBDN01 (AC+PBS, ST-012) configurado con 7 specs limpias del CERST-012.")
print("Verificar en staging: https://stagingfc.amunet.com.mx/odoo/quality-checks")
