"""
CORRECCIÓN acceptance_criteria MICAJ — Configuración fuente (producción)
========================================================================
El fix de 2026-09-23 (fix_micaj_etiquetas_analisis_prod.py) corrigió los
registros existentes de amunet_quality_test_line_detail en producción, pero
NO actualizó la fuente (amunet_quality_parameter_specification_config).

Por eso, cada análisis nuevo de MICAJ seguía naciendo con criterios
intercambiados:
  - Ancho (rango 105-115): "200 mm ±5 mm"  ← incorrecto
  - Largo (rango 195-205): "110 mm ±5 mm"  ← incorrecto

Este script corrige los registros de config (la fuente) para que todos los
análisis futuros hereden los criterios correctos. Los análisis existentes que
aún tengan los criterios invertidos también se corrigen.

Solicitado por: Diana Flores — Control de Calidad, 2026-09-28
"""

import logging
_logger = logging.getLogger(__name__)

cr = env.cr

# 1. Corregir la configuración fuente (amunet_quality_parameter_specification_config)
cr.execute("""
UPDATE amunet_quality_parameter_specification_config cfg
SET acceptance_criteria = '110 mm ±5 mm'
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON rel.product_tmpl_id = pt.id
WHERE cfg.product_parameter_rel_id = rel.id
  AND pt.default_code LIKE 'MICAJ%%'
  AND cfg.specification_name = 'Ancho'
  AND cfg.min_value = 105
  AND (cfg.acceptance_criteria != '110 mm ±5 mm' OR cfg.acceptance_criteria IS NULL);
""")
n_ancho_cfg = cr.rowcount
_logger.info(f"Config fuente — Ancho corregidos: {n_ancho_cfg}")

cr.execute("""
UPDATE amunet_quality_parameter_specification_config cfg
SET acceptance_criteria = '200 mm ±5 mm'
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON rel.product_tmpl_id = pt.id
WHERE cfg.product_parameter_rel_id = rel.id
  AND pt.default_code LIKE 'MICAJ%%'
  AND cfg.specification_name = 'Largo'
  AND cfg.min_value = 195
  AND (cfg.acceptance_criteria != '200 mm ±5 mm' OR cfg.acceptance_criteria IS NULL);
""")
n_largo_cfg = cr.rowcount
_logger.info(f"Config fuente — Largo corregidos: {n_largo_cfg}")

# 2. Corregir análisis existentes que aún tengan criterios invertidos
cr.execute("""
UPDATE amunet_quality_test_line_detail tld
SET acceptance_criteria = '110 mm ±5 mm'
FROM amunet_quality_check qc
JOIN product_product pp ON qc.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
WHERE tld.check_id = qc.id
  AND pt.default_code LIKE 'MICAJ%%'
  AND tld.name = 'Ancho'
  AND tld.min_value = 105
  AND (tld.acceptance_criteria != '110 mm ±5 mm' OR tld.acceptance_criteria IS NULL);
""")
n_ancho_det = cr.rowcount

cr.execute("""
UPDATE amunet_quality_test_line_detail tld
SET acceptance_criteria = '200 mm ±5 mm'
FROM amunet_quality_check qc
JOIN product_product pp ON qc.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
WHERE tld.check_id = qc.id
  AND pt.default_code LIKE 'MICAJ%%'
  AND tld.name = 'Largo'
  AND tld.min_value = 195
  AND (tld.acceptance_criteria != '200 mm ±5 mm' OR tld.acceptance_criteria IS NULL);
""")
n_largo_det = cr.rowcount

env.cr.commit()

print(f"""
✓ Fix acceptance_criteria MICAJ aplicado:

  Configuración fuente:
    Ancho corregidos: {n_ancho_cfg}
    Largo corregidos: {n_largo_cfg}

  Análisis existentes:
    Ancho corregidos: {n_ancho_det}
    Largo corregidos: {n_largo_det}

  Desde ahora todo análisis nuevo de MICAJ hereda los criterios correctos.
""")
