"""
Limpia y configura los parámetros de QC de STBTR02
(Vial individual tracto respiratorio, ST-035)
según el CERST-035.

Valores del CERST-035:
  MAVI-13  — Partículas en solución: Sin partículas suspendidas  ← ya correcto
  MAVI-17  — Gotas obtenidas: ≥10 gotas                         ← ya correcto
  MGA 0181 — Color: Solución incolora                            ← corregir criterio
  MGA 0701 — pH: 9 ± 0.5 (8.5–9.5)                             ← ya correcto
  MGA 0981 — Variación de volumen: ≥ 500 µl                     ← corregir tipo y rango

IDs de rels:
  MAVI-13=275, MAVI-17=278, MGA 0181=277, MGA 0701=276, MGA 0981=274

Canonical spec IDs (únicos con FK en tld):
  78178 (MAVI-13), 78181 (MAVI-17), 78180 (MGA 0181),
  78179 (MGA 0701), 78228 (MGA 0981)

Idempotente — seguro de correr más de una vez.
Correr UNA VEZ después del deploy a producción.
"""

# ── 1. Corregir MGA 0181: criterio debe ser "Solución incolora" ─────────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET acceptance_criteria = 'Solución incolora',
        specification_name  = 'Color de solución',
        write_date          = NOW()
    WHERE id = 78180
""")
print(f"MGA 0181 Color (id=78180): criterio → 'Solución incolora'")

# ── 2. Corregir MGA 0981: binary_selection → numeric_range ≥ 500 µl ─────────
env.cr.execute("""
    UPDATE amunet_quality_parameter_specification_config
    SET evaluation_type     = 'numeric_range',
        min_value           = 500,
        max_value           = 999999,
        acceptance_criteria = '≥ 500 µl',
        specification_name  = 'Variación de volumen',
        write_date          = NOW()
    WHERE id = 78228
""")
print(f"MGA 0981 Volumen (id=78228): → numeric_range, ≥500 µl")

# ── 3. Eliminar specs duplicadas (sin FK refs en tld) ────────────────────────
DELETE_MAVI13  = [643,75691,75907,76123,76479,76695,76911,77127,77653,77962]
DELETE_MAVI17  = [73077,75529,75694,75910,76219,76289,76482,76698,76914,77130,77656,77965]
DELETE_MGA0181 = [3156,73076,75693,75909,76125,76481,76697,76913,77129,77655,77964]
DELETE_MGA0701 = [73078,75528,75692,75908,76218,76288,76480,76696,76912,77128,77654,77963]
DELETE_MGA0981 = [73079,75690,75906,76217,76287,76478,76694,76910,77126,77652,77961]

for label, ids in [
    ('MAVI-13',  DELETE_MAVI13),
    ('MAVI-17',  DELETE_MAVI17),
    ('MGA 0181', DELETE_MGA0181),
    ('MGA 0701', DELETE_MGA0701),
    ('MGA 0981', DELETE_MGA0981),
]:
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config WHERE id = ANY(%s)",
        (ids,)
    )
    print(f"{label}: {env.cr.rowcount} specs duplicadas eliminadas")

env.cr.commit()
print("\nLISTO — STBTR02 (ST-035) configurado con 5 specs limpias del CERST-035.")
print("Verificar en staging: https://stagingfc.amunet.com.mx/odoo/quality-checks")
