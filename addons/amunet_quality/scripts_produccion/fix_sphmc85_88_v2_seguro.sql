-- ============================================================
-- SCRIPT v2 SEGURO: SPHMC85-88 — sin cancelaciones, sin borrar análisis
-- Preparado: 2026-09-29  |  Aplicar en amunet_prod
-- ============================================================
-- Qué hace:
--   PARTE 1: Agrega 3 MAVI-04 estándar (seq=10) a la raíz de SPHMC85/86/87/88
--            Corrige tipo MAVI-11 de SPHMC85 (UPDATE, no delete)
--            Corrige valores MAVI-09 de SPHMC85 (UPDATE, no delete)
--   PARTE 2: En QC/00503/504/505 borra SOLO las 4 líneas no estándar de MAVI-04
--            (Letra, Letra adecuada, Sellado, Deformidad duplicada)
--            Las 3 líneas correctas (Manchas, Rasgaduras, Deformidad) quedan intactas
--            con sus veredictos ya capturados.
-- NO cancela ningún análisis. NO borra spec_configs referenciados.
-- ============================================================

BEGIN;

-- ============================================================
-- PARTE 1: RAÍZ — agregar MAVI-04 seq=10 (idempotente)
-- ============================================================

INSERT INTO amunet_quality_parameter_specification_config (
  product_parameter_rel_id, specification_id, sequence, uom_id,
  product_tmpl_id, parameter_id, company_id,
  specification_name, evaluation_type, acceptance_criteria,
  binary_option_pass, binary_option_fail,
  binary_expected_option, config_summary,
  min_value, max_value,
  create_uid, write_uid, create_date, write_date
)
SELECT
  new_ppr.id,
  ref.specification_id, ref.sequence, ref.uom_id,
  new_ppr.product_tmpl_id, ref.parameter_id, ref.company_id,
  ref.specification_name, ref.evaluation_type, ref.acceptance_criteria,
  ref.binary_option_pass, ref.binary_option_fail,
  ref.binary_expected_option, ref.config_summary,
  ref.min_value, ref.max_value,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_specification_config ref
JOIN amunet_quality_parameter_product_rel ref_ppr ON ref_ppr.id = ref.product_parameter_rel_id
JOIN product_template ref_pt ON ref_pt.id = ref_ppr.product_tmpl_id
JOIN amunet_quality_check_parameter cp ON cp.id = ref_ppr.parameter_id
JOIN amunet_quality_parameter_product_rel new_ppr ON new_ppr.parameter_id = ref_ppr.parameter_id
JOIN product_template new_pt ON new_pt.id = new_ppr.product_tmpl_id
WHERE ref_pt.default_code = 'SPHMC62'
  AND cp.code = 'MAVI-04'
  AND ref.sequence < 99
  AND new_pt.default_code IN ('SPHMC85','SPHMC86','SPHMC87','SPHMC88')
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config e
    WHERE e.product_parameter_rel_id = new_ppr.id
      AND e.specification_name = ref.specification_name
      AND e.sequence < 99
  );
-- Esperado: INSERT 0 12 (3 por cada uno de los 4 productos)

-- MAVI-11: corregir tipo de evaluación (solo SPHMC85, si aún es mavi_11_height)
UPDATE amunet_quality_parameter_specification_config
SET evaluation_type = 'conditional_numeric_range', write_date = NOW()
WHERE product_parameter_rel_id = (
  SELECT ppr.id FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC85' AND cp.code = 'MAVI-11'
)
AND evaluation_type = 'mavi_11_height';

-- MAVI-09 SPHMC85: corregir valores (si aún tienen 0/0)
UPDATE amunet_quality_parameter_specification_config
SET acceptance_criteria = '1 a 30 segundos',
    binary_option_pass  = 'Captura [    ] segundos',
    binary_option_fail  = 'No captura [    ] segundos',
    min_value = 1, max_value = 30, write_date = NOW()
WHERE product_parameter_rel_id = (
  SELECT ppr.id FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC85' AND cp.code = 'MAVI-09'
)
AND specification_name = 'Tiempo de liberación' AND sequence < 99;

UPDATE amunet_quality_parameter_specification_config
SET acceptance_criteria = '30 a 180 segundos',
    binary_option_pass  = 'Captura [    ] segundos',
    binary_option_fail  = 'No captura [    ] segundos',
    min_value = 30, max_value = 180, write_date = NOW()
WHERE product_parameter_rel_id = (
  SELECT ppr.id FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC85' AND cp.code = 'MAVI-09'
)
AND specification_name = 'Tiempo de migración' AND sequence < 99;

-- ============================================================
-- PARTE 2: Limpiar líneas no estándar de QC/00503, 00504, 00505
-- ============================================================

-- 2a) MAVI-04: borrar las 4 líneas no estándar (Letra, Letra adecuada, Sellado, Deformidad dup.)
--     Las 3 correctas (Manchas, Rasgaduras, Deformidad) quedan intactas con sus veredictos
DELETE FROM amunet_quality_test_line_detail
WHERE check_id IN (
  SELECT id FROM amunet_quality_check
  WHERE name IN ('QC/2026/00503','QC/2026/00504','QC/2026/00505')
)
AND specification_config_id IN (
  SELECT psc.id
  FROM amunet_quality_parameter_specification_config psc
  JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = psc.product_parameter_rel_id
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code IN ('SPHMC86','SPHMC87','SPHMC88')
    AND cp.code = 'MAVI-04'
    AND psc.specification_name NOT IN ('Manchas y/o suciedad','Rasgaduras','Deformidad o deterioro')
);
-- Esperado: DELETE 12 (4 líneas × 3 análisis)

-- 2b) MAVI-09: borrar las 2 líneas duplicadas seq=99 (sin criterio, pendientes)
--     Las 2 correctas seq=10 (Liberación 1-30s, Migración 30-180s) quedan intactas
DELETE FROM amunet_quality_test_line_detail
WHERE check_id IN (
  SELECT id FROM amunet_quality_check
  WHERE name IN ('QC/2026/00503','QC/2026/00504','QC/2026/00505')
)
AND specification_config_id IN (
  SELECT psc.id
  FROM amunet_quality_parameter_specification_config psc
  JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = psc.product_parameter_rel_id
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code IN ('SPHMC86','SPHMC87','SPHMC88')
    AND cp.code = 'MAVI-09'
    AND psc.sequence >= 99
);
-- Esperado: DELETE 6 (2 líneas × 3 análisis)

-- 2c) MAVI-11: borrar la entrada duplicada "Vial - Altura" (mavi_11_height, seq=40)
--     La correcta "Altura 6 u 8 cm (según aplique)" (conditional_numeric_range) queda intacta
DELETE FROM amunet_quality_test_line_detail
WHERE check_id IN (
  SELECT id FROM amunet_quality_check
  WHERE name IN ('QC/2026/00503','QC/2026/00504','QC/2026/00505')
)
AND specification_config_id IN (
  SELECT psc.id
  FROM amunet_quality_parameter_specification_config psc
  JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = psc.product_parameter_rel_id
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code IN ('SPHMC86','SPHMC87','SPHMC88')
    AND cp.code = 'MAVI-11'
    AND psc.evaluation_type = 'mavi_11_height'
);
-- Esperado: DELETE 3 (1 línea × 3 análisis)

-- ============================================================
-- VERIFICACIÓN FINAL
-- ============================================================

-- Raíz: debe mostrar 3 en MAVI-04 para los 4 productos
SELECT pt.default_code,
  COUNT(psc.id) FILTER (WHERE cp.code='MAVI-04' AND psc.sequence < 99) as m04,
  COUNT(psc.id) FILTER (WHERE cp.code='MAVI-07' AND psc.sequence < 99) as m07,
  COUNT(psc.id) FILTER (WHERE cp.code='MAVI-09' AND psc.sequence < 99) as m09,
  COUNT(psc.id) FILTER (WHERE cp.code='MAVI-11' AND psc.sequence < 99) as m11
FROM product_template pt
JOIN amunet_quality_parameter_product_rel ppr ON ppr.product_tmpl_id = pt.id
JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
LEFT JOIN amunet_quality_parameter_specification_config psc ON psc.product_parameter_rel_id = ppr.id
WHERE pt.default_code IN ('SPHMC85','SPHMC86','SPHMC87','SPHMC88')
  AND cp.code IN ('MAVI-04','MAVI-07','MAVI-09','MAVI-11')
GROUP BY pt.default_code ORDER BY pt.default_code;

-- Análisis activos: deben mostrar 3 líneas MAVI-04 (solo estándar)
SELECT qc.name, COUNT(tld.id) as lineas_mavi04
FROM amunet_quality_check qc
JOIN amunet_quality_test_line_detail tld ON tld.check_id = qc.id
JOIN amunet_quality_parameter_specification_config psc ON psc.id = tld.specification_config_id
JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = psc.product_parameter_rel_id
JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
WHERE qc.name IN ('QC/2026/00503','QC/2026/00504','QC/2026/00505')
  AND cp.code = 'MAVI-04'
GROUP BY qc.name ORDER BY qc.name;

COMMIT;
