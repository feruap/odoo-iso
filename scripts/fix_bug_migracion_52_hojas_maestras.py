#!/usr/bin/env python3
"""
=============================================================
CORRECCIÓN BUG MIGRACIÓN 52.0 — HOJAS MAESTRAS SPHMC/SPHMT
=============================================================

Problema:
  La migración 19.0.3.52.0 confundió IDs de product.product con
  product.template, lo que generó líneas de prueba incorrectas
  (estructura de PT: MGA-0486, INC-002, MAVI-04 de empaque) en
  análisis de hojas maestras SPHMC/SPHMT.

  El CATÁLOGO (qc_parameter_rel_ids y spec_configs) NO fue tocado
  y está correcto para cada producto.

Solución:
  1. Borrar las líneas incorrectas de cada análisis afectado.
  2. Llamar _load_product_parameters() para regenerarlas desde
     el catálogo correcto de cada producto.

Cómo ejecutar (en el servidor de producción):
  cd /opt/odoo/production
  docker exec -i odoo-production bash -c \
    "odoo shell -d amunet_prod --no-http" \
    < /ruta/a/fix_bug_migracion_52_hojas_maestras.py

O desde el shell interactivo de Odoo, pegar el bloque principal.

Fecha: 2026-09-11
Solicitado por: Diana Flores — Control de Calidad
=============================================================
"""

import logging
_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Buscar dinámicamente los análisis afectados:
# SPHMC o SPHMT que tengan MGA-0486 o INC-002 (parámetros de PT)
# en estado que no sea cancelado ni aprobado (done).
# ------------------------------------------------------------------

# Obtener IDs de los parámetros incorrectos por código (robusto entre BD)
param_incorrectos = env['amunet.quality.check.parameter'].search([
    ('code', 'in', ['MGA-0486', 'INC-002'])
])
param_ids = param_incorrectos.ids

if not param_ids:
    print("ERROR: No se encontraron los parámetros MGA-0486 / INC-002.")
    print("Verificar que los códigos sean correctos en esta base de datos.")
else:
    print(f"Parámetros incorrectos encontrados: {[(p.code, p.id) for p in param_incorrectos]}")

    # Análisis afectados (excluyendo cancelados y ya aprobados)
    afectados = env['amunet.quality.check'].search([
        ('product_id.default_code', 'like', 'SPHM%'),
        ('test_line_ids.parameter_id', 'in', param_ids),
        ('state', 'not in', ['cancel', 'done']),
    ])

    draft_qcs       = afectados.filtered(lambda q: q.state == 'draft')
    in_progress_qcs = afectados.filtered(lambda q: q.state == 'in_progress')

    print("=" * 60)
    print(f"ANÁLISIS AFECTADOS: {len(afectados)} total")
    print(f"  En borrador (draft):       {len(draft_qcs)}")
    print(f"  En progreso (in_progress): {len(in_progress_qcs)}")
    print("=" * 60)

    if in_progress_qcs:
        print("\n⚠  ADVERTENCIA — ANÁLISIS EN PROGRESO:")
        for qc in in_progress_qcs:
            print(f"   {qc.name}  ({qc.product_id.default_code})")
        print("   Los datos capturados en estos análisis SON INVÁLIDOS")
        print("   (se capturaron contra criterios de PT, no de hoja maestra).")
        print("   Al corregirlos se borrarán; el analista deberá recapturar.\n")

    # ------------------------------------------------------------------
    # Función de corrección: borra líneas incorrectas y regenera
    # ------------------------------------------------------------------
    def fix_analysis(qc):
        nombre = f"{qc.name} ({qc.product_id.default_code})"
        lineas_antes = len(qc.test_line_ids)
        qc.test_line_ids.unlink()          # borra líneas y detalles en cascada
        qc._load_product_parameters()     # regenera desde catálogo correcto
        lineas_despues = len(qc.test_line_ids)
        print(f"  ✓ {nombre}: {lineas_antes} líneas incorrectas → {lineas_despues} líneas nuevas")

    # ------------------------------------------------------------------
    # 1. Corregir los que están en borrador
    # ------------------------------------------------------------------
    if draft_qcs:
        print(f"\n--- Corrigiendo {len(draft_qcs)} análisis en DRAFT ---")
        for qc in draft_qcs:
            fix_analysis(qc)
        env.cr.commit()
        print("✓ Commit realizado para análisis en draft.")

    # ------------------------------------------------------------------
    # 2. Corregir los que están en progreso
    # ------------------------------------------------------------------
    if in_progress_qcs:
        print(f"\n--- Corrigiendo {len(in_progress_qcs)} análisis IN_PROGRESS ---")
        for qc in in_progress_qcs:
            fix_analysis(qc)
        env.cr.commit()
        print("✓ Commit realizado para análisis en progreso.")
        print("\nACCIÓN REQUERIDA: Avisar a los analistas que deben")
        print("volver a capturar los siguientes análisis:")
        for qc in in_progress_qcs:
            print(f"  - {qc.name}  ({qc.product_id.default_code})")

    print("\n" + "=" * 60)
    print("CORRECCIÓN COMPLETADA")
    print("=" * 60)
    print("\nVerificación rápida post-ejecución:")
    print("  SELECT qc.name, pp.default_code, COUNT(tl.id) as lineas")
    print("  FROM amunet_quality_check qc")
    print("  JOIN product_product pp ON pp.id = qc.product_id")
    print("  LEFT JOIN amunet_quality_test_line tl ON tl.check_id = qc.id")
    print("  WHERE pp.default_code LIKE 'SPHM%' AND qc.state != 'cancel'")
    print("  GROUP BY qc.id, qc.name, pp.default_code ORDER BY qc.id;")
