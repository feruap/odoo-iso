#!/usr/bin/env python3
"""
CORRECCIÓN: MAVI-07 con mavi_07_ternary en lugar de vama_multi_check
Análisis: QC/2026/00323 (id=898), Producto: DMENG01

Problema: La migración 52 cargó las líneas de MAVI-07 usando rel_id=4425
(solo mavi_07_ternary) en lugar de rel_id=3421 (vama_multi_check correcto).

Solución: Borrar los 2 detalles incorrectos de mavi_07_ternary y recrear
desde el catálogo correcto (vama_multi_check, rel_id=3421).

Cómo ejecutar:
  docker exec -i odoo-production bash -c "odoo shell -d amunet_prod --no-http" \
    < /ruta/a/fix_mavi07_dmeng01_analisis_898.py
"""

qc = env['amunet.quality.check'].browse(898)
print(f"Análisis: {qc.name} — {qc.product_id.default_code} — Estado: {qc.state}")

# Línea de test MAVI-07
mavi07_line = qc.test_line_ids.filtered(lambda l: l.code == 'MAVI-07')
if not mavi07_line:
    print("ERROR: No se encontró línea MAVI-07 en el análisis 898")
else:
    print(f"Línea MAVI-07 encontrada: id={mavi07_line.id}")
    detalles_antes = mavi07_line.detail_line_ids
    print(f"Detalles actuales ({len(detalles_antes)}):")
    for d in detalles_antes:
        print(f"  id={d.id} tipo={d.evaluation_type} criterio={d.acceptance_criteria}")

    # Borrar detalles incorrectos (mavi_07_ternary)
    detalles_antes.unlink()
    print("✓ Detalles incorrectos eliminados")

    # Obtener spec_configs correctas de vama_multi_check (rel_id=3421)
    specs = env['amunet.quality.parameter.specification.config'].search([
        ('product_parameter_rel_id', '=', 3421),
        ('evaluation_type', '=', 'vama_multi_check'),
    ], order='id asc')

    print(f"\nSpec configs a cargar ({len(specs)}):")
    for s in specs:
        print(f"  id={s.id} criterio={s.acceptance_criteria}")

    # Crear nuevos detalles con vama_multi_check
    for i, spec in enumerate(specs):
        env['amunet.quality.test.line.detail'].create({
            'test_line_id': mavi07_line.id,
            'check_id': qc.id,
            'specification_config_id': spec.id,
            'specification_id': spec.specification_id.id,
            'sequence': (i + 1) * 10,
            'name': spec.specification_name or spec.acceptance_criteria,
            'evaluation_type': spec.evaluation_type,
            'acceptance_criteria': spec.acceptance_criteria,
            'text_phrase_mapping': spec.text_phrase_mapping,
            'expected_options': spec.expected_options,
        })

    env.cr.commit()
    print(f"✓ {len(specs)} detalles de vama_multi_check creados")

    detalles_nuevos = mavi07_line.detail_line_ids
    print(f"\nDetalles nuevos ({len(detalles_nuevos)}):")
    for d in detalles_nuevos:
        print(f"  id={d.id} tipo={d.evaluation_type} criterio={d.acceptance_criteria}")

print("\nCORRECCIÓN COMPLETADA — Verificar en https://fc.amunet.com.mx/odoo/action-937/898")
