"""
Limpia y reconfigura los parámetros de QC de SPHMC75 y SPHMC76
(Antidoping Sangre 2 y 3 parámetros).

Problema: specs duplicadas masivas (125 de MAVI-09 en c/u, 19 de MAVI-04, 14 de MAVI-11).
Sin registros TLD activos → se puede limpiar completamente y recrear.

Confirmado por Diana Flores, 2026-08-06:
  MAVI-09 — Liberación: 1–30 s, Migración: 30–180 s
  MAVI-07 — Competitiva: Pos = línea control sola (#5), Neg = línea control + prueba (#1-4)
  MAVI-07 ya tiene los 2 specs correctos (IDs 78908/78909 y 78910/78911) — no se toca.
  MAVI-11 — pendiente confirmación de dimensiones por Diana.

Idempotente — seguro de correr más de una vez.
"""

PRODUCTOS = {
    'SPHMC75': {
        'rel_mavi04': 3186,
        'rel_mavi09': 3189,
        'rel_mavi11': 3190,
    },
    'SPHMC76': {
        'rel_mavi04': 3187,
        'rel_mavi09': 3192,
        'rel_mavi11': 3193,
    },
}

for codigo, cfg in PRODUCTOS.items():
    print(f"\n── {codigo} ──────────────────────────────────────")

    # ── MAVI-04: borrar todo y recrear las 5 specs estándar ────────────────
    rel04 = cfg['rel_mavi04']
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config "
        "WHERE product_parameter_rel_id = %s", (rel04,)
    )
    print(f"  MAVI-04: {env.cr.rowcount} specs eliminadas")

    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, min_value, max_value, acceptance_criteria, sequence,
           create_date, write_date, create_uid, write_uid)
        VALUES
          (%s,   1, 'Polvo',                  'binary_selection', 0, 0, 'Sin polvo',                  10, NOW(), NOW(), 1, 1),
          (%s, 170, 'Rasgaduras',             'binary_selection', 0, 0, 'Sin rasgaduras',             99, NOW(), NOW(), 1, 1),
          (%s, 171, 'Manchas y/o suciedad',   'binary_selection', 0, 0, 'Sin manchas y/o suciedad',   99, NOW(), NOW(), 1, 1),
          (%s, 175, 'Deformidad o deterioro', 'binary_selection', 0, 0, 'Sin deformidad o deterioro', 99, NOW(), NOW(), 1, 1),
          (%s, 190, 'Sellado',                'binary_selection', 0, 0, '',                            99, NOW(), NOW(), 1, 1)
    """, (rel04, rel04, rel04, rel04, rel04))
    print(f"  MAVI-04: 5 specs estándar creadas")

    # ── MAVI-09: borrar todo y recrear las 2 specs correctas ───────────────
    rel09 = cfg['rel_mavi09']
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config "
        "WHERE product_parameter_rel_id = %s", (rel09,)
    )
    print(f"  MAVI-09: {env.cr.rowcount} specs eliminadas")

    env.cr.execute("""
        INSERT INTO amunet_quality_parameter_specification_config
          (product_parameter_rel_id, specification_id, specification_name,
           evaluation_type, min_value, max_value, acceptance_criteria, sequence,
           create_date, write_date, create_uid, write_uid)
        VALUES
          (%s, 146, 'Liberación de conjugado', 'numeric_range', 1,  30,  '1 a 30 segundos',   10, NOW(), NOW(), 1, 1),
          (%s, 126, 'Migración de conjugado',  'numeric_range', 30, 180, '30 a 180 segundos', 20, NOW(), NOW(), 1, 1)
    """, (rel09, rel09))
    print(f"  MAVI-09: 2 specs creadas (Lib 1-30 s / Mig 30-180 s)")

    # ── MAVI-11: limpiar duplicados (dimensiones se confirman con Diana) ───
    rel11 = cfg['rel_mavi11']
    env.cr.execute(
        "DELETE FROM amunet_quality_parameter_specification_config "
        "WHERE product_parameter_rel_id = %s", (rel11,)
    )
    print(f"  MAVI-11: {env.cr.rowcount} specs eliminadas (se configurarán cuando Diana confirme dimensiones)")

env.cr.commit()
print("\nLISTO — SPHMC75 y SPHMC76 limpios.")
print("MAVI-07 no se tocó (ya correcto). MAVI-11 pendiente dimensiones.")
print("Verificar: https://stagingfc.amunet.com.mx/odoo/inventory/products")
