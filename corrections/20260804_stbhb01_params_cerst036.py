"""
Limpia y configura los parámetros de QC de STBHB01
(Vial individual solución corrimiento HbA1c, ST-036)
según el CERST-036.

Valores del CERST-036:
  MAVI-09 — Liberación: 10–90 s  (HbA1c tiene tiempos distintos al estándar)
  MAVI-09 — Migración:  40–190 s
  MAVI-07 — Muestra negativa: "#5 y/o #1-4 (patrón PRB-01)"
  MAVI-07 — Muestra positiva: "#1-4 y/o #5 (patrón PRB-01)"
  MAVI-13 — Partículas en solución: Sin partículas suspendidas
  MGA 0701 — pH: 9 ± 1.0 (8.0–10.0)
  MGA 0981 — Variación de volumen: ≥ 1 mL

IDs de rels:
  MAVI-07=283, MAVI-09=282, MAVI-13=280, MGA 0701=281, MGA 0981=279

Canonical spec IDs (únicos con FK en tld):
  78187 (MAVI-07→Muestra neg), 78185 (Liberación), 78186 (Migración),
  78183 (MAVI-13), 78184 (MGA 0701), 78182 (MGA 0981)

Idempotente — seguro de correr más de una vez.
Correr UNA VEZ después del deploy a producción.
"""

# ── 1. Actualizar specs canónicas ─────────────────────────────────────────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id    = 146,
        specification_name  = 'Liberación de conjugado',
        evaluation_type     = 'numeric_range',
        min_value           = 10,
        max_value           = 90,
        acceptance_criteria = '10 a 90 segundos',
        sequence            = 10,
        write_date          = NOW()
    WHERE id = 78185
""")
print("MAVI-09 Liberación (id=78185): → 10–90 s")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id    = 126,
        specification_name  = 'Migración de conjugado',
        evaluation_type     = 'numeric_range',
        min_value           = 40,
        max_value           = 190,
        acceptance_criteria = '40 a 190 segundos',
        sequence            = 20,
        write_date          = NOW()
    WHERE id = 78186
""")
print("MAVI-09 Migración (id=78186): → 40–190 s")

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
    WHERE id = 78187
""")
print("MAVI-07 Muestra negativa (id=78187): actualizado")

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
    WHERE id = 78183
""")
print("MAVI-13 Partículas (id=78183): Sin partículas suspendidas")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id    = 87,
        specification_name  = 'pH de solución',
        evaluation_type     = 'numeric_range',
        min_value           = 8.0,
        max_value           = 10.0,
        acceptance_criteria = '9 ± 1.0',
        sequence            = 10,
        write_date          = NOW()
    WHERE id = 78184
""")
print("MGA 0701 pH (id=78184): → 8.0–10.0")

env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET specification_id    = 86,
        specification_name  = 'Variación de volumen',
        evaluation_type     = 'numeric_range',
        min_value           = 1.0,
        max_value           = 999999,
        acceptance_criteria = '≥ 1 mL',
        sequence            = 10,
        write_date          = NOW()
    WHERE id = 78182
""")
print("MGA 0981 Volumen (id=78182): → ≥ 1 mL")

# ── 2. Insertar "Muestra positiva" para MAVI-07 (rel_id=283) ─────────────────
env.cr.execute("""
    INSERT INTO amunet_quality_parameter_specification_config
      (product_parameter_rel_id, specification_id, specification_name,
       evaluation_type, min_value, max_value, acceptance_criteria, sequence,
       create_date, write_date, create_uid, write_uid)
    VALUES (283, 629, 'Muestra positiva', 'mavi_07_ternary', 0, 0,
            '#1-4 y/o #5 (patrón PRB-01)', 10, NOW(), NOW(), 1, 1)
    ON CONFLICT DO NOTHING
""")
print("MAVI-07 Muestra positiva: insertada (rel_id=283)")

# ── 3. Eliminar specs duplicadas ──────────────────────────────────────────────
DELETE_MAVI07 = [
    74832,75396,75397,75531,75532,75700,75701,75916,75917,76224,76225,
    76294,76295,76488,76489,76704,76705,76920,76921,77136,77137,77662,77663,77971,77972,
]
DELETE_MAVI09 = [
    650,651,75698,75699,75914,75915,76222,76223,76292,76293,76486,76487,
    76702,76703,76918,76919,77134,77135,77660,77661,77969,77970,
]
DELETE_MAVI13 = [648,75696,75912,76128,76484,76700,76916,77132,77658,77967]
DELETE_MGA0701 = [73064,75530,75697,75913,76221,76291,76485,76701,76917,77133,77659,77968]
DELETE_MGA0981 = [73065,75695,75911,76220,76290,76483,76699,76915,77131,77657,77966]

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
print("\nLISTO — STBHB01 (HbA1c, ST-036) configurado con 7 specs limpias del CERST-036.")
print("Verificar en staging: https://stagingfc.amunet.com.mx/odoo/quality-checks")
