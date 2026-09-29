-- ============================================================
-- SCRIPT: Correcciones MAVI-04/09/11 — SPHMC34, SPHMC78, SPHMC79, SPHMC80
-- Preparado: 2026-09-29  |  Aplicar en amunet_prod, Fernando/desarrollo
-- Validado en staging: todos los cambios confirmados
-- ============================================================

BEGIN;

-- ============================================================
-- SPHMC80: Cancelar borrador QC/2026/00322
-- (sus líneas tienen MAVI-04 en seq-99 — quedarán obsoletas con el fix)
-- ============================================================
UPDATE amunet_quality_check SET state = 'cancel', write_date = NOW()
WHERE name = 'QC/2026/00322'
  AND state IN ('draft','in_progress','confirm');

-- ============================================================
-- SPHMC78 (HPV E7): borrar 2 entradas MAVI-04 extra (seq 40 y 50)
-- Son entradas con specification_name NOT IN estándar — no usadas en análisis
-- ============================================================
DELETE FROM amunet_quality_parameter_specification_config
WHERE product_parameter_rel_id = (
  SELECT ppr.id FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC78' AND cp.code = 'MAVI-04'
)
AND sequence BETWEEN 11 AND 98;

-- ============================================================
-- SPHMC79 (CARBA 5 en 1): igual que SPHMC78
-- ============================================================
DELETE FROM amunet_quality_parameter_specification_config
WHERE product_parameter_rel_id = (
  SELECT ppr.id FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC79' AND cp.code = 'MAVI-04'
)
AND sequence BETWEEN 11 AND 98;

-- ============================================================
-- SPHMC80 (ToRCH Herpes 1/2): agregar MAVI-04 seq-10 + limpiar extras
-- ============================================================

-- Borrar MAVI-11 extra (mavi_11_height, debería ser solo 1 conditional_numeric_range)
DELETE FROM amunet_quality_parameter_specification_config
WHERE product_parameter_rel_id = (
  SELECT ppr.id FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC80' AND cp.code = 'MAVI-11'
)
AND evaluation_type = 'mavi_11_height'
AND sequence BETWEEN 11 AND 98;

-- Borrar MAVI-04 seq-99 no estándar (Letra, Sellado, Adecuado, etc.)
DELETE FROM amunet_quality_parameter_specification_config
WHERE product_parameter_rel_id = (
  SELECT ppr.id FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC80' AND cp.code = 'MAVI-04'
)
AND sequence >= 99
AND specification_name NOT IN (
    'Manchas y/o suciedad', 'Rasgaduras', 'Deformidad o deterioro'
);

-- Agregar MAVI-04 seq-10 (copia de SPHMC62, idempotente)
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
JOIN amunet_quality_parameter_product_rel new_ppr
  ON new_ppr.parameter_id = ref_ppr.parameter_id
JOIN product_template new_pt ON new_pt.id = new_ppr.product_tmpl_id
WHERE ref_pt.default_code = 'SPHMC62'
  AND cp.code = 'MAVI-04'
  AND ref.sequence < 99
  AND new_pt.default_code = 'SPHMC80'
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config e
    WHERE e.product_parameter_rel_id = new_ppr.id
      AND e.specification_name = ref.specification_name
      AND e.sequence < 99
  );

-- ============================================================
-- SPHMC34 (CA 15-3): arreglo completo
-- ============================================================

-- Mover NULL-seq MAVI-04 a seq=99 (historial)
UPDATE amunet_quality_parameter_specification_config
SET sequence = 99, write_date = NOW()
WHERE product_parameter_rel_id = (
  SELECT ppr.id FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC34' AND cp.code = 'MAVI-04'
)
AND sequence IS NULL;

-- Agregar MAVI-04 seq-10 (copia de SPHMC62, idempotente)
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
JOIN amunet_quality_parameter_product_rel new_ppr
  ON new_ppr.parameter_id = ref_ppr.parameter_id
JOIN product_template new_pt ON new_pt.id = new_ppr.product_tmpl_id
WHERE ref_pt.default_code = 'SPHMC62'
  AND cp.code = 'MAVI-04'
  AND ref.sequence < 99
  AND new_pt.default_code = 'SPHMC34'
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config e
    WHERE e.product_parameter_rel_id = new_ppr.id
      AND e.specification_name = ref.specification_name
      AND e.sequence < 99
  );

-- Corregir MAVI-09: renombrar a nombres estándar + corregir criterios
UPDATE amunet_quality_parameter_specification_config
SET specification_name = 'Tiempo de liberación',
    acceptance_criteria = '1 a 30 segundos',
    binary_option_pass  = 'Captura [    ] segundos',
    binary_option_fail  = 'No captura [    ] segundos',
    write_date = NOW()
WHERE product_parameter_rel_id = (
  SELECT ppr.id FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC34' AND cp.code = 'MAVI-09'
)
AND specification_name = 'Liberación de conjugado';

UPDATE amunet_quality_parameter_specification_config
SET specification_name = 'Tiempo de migración',
    acceptance_criteria = '30 a 180 segundos',
    max_value = 180,
    binary_option_pass  = 'Captura [    ] segundos',
    binary_option_fail  = 'No captura [    ] segundos',
    write_date = NOW()
WHERE product_parameter_rel_id = (
  SELECT ppr.id FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC34' AND cp.code = 'MAVI-09'
)
AND specification_name = 'Migración de conjugado';

-- Corregir MAVI-11: cambiar tipo de mavi_11_height a conditional_numeric_range
UPDATE amunet_quality_parameter_specification_config
SET evaluation_type = 'conditional_numeric_range',
    write_date = NOW()
WHERE product_parameter_rel_id = (
  SELECT ppr.id FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC34' AND cp.code = 'MAVI-11'
)
AND evaluation_type = 'mavi_11_height';

-- ============================================================
-- VERIFICACIÓN FINAL — resultado esperado: todas en 3-2-2-1
-- ============================================================
SELECT pt.default_code,
  COUNT(psc.id) FILTER (WHERE cp.code='MAVI-04' AND psc.sequence < 99) as m04,
  COUNT(psc.id) FILTER (WHERE cp.code='MAVI-07' AND psc.sequence < 99) as m07,
  COUNT(psc.id) FILTER (WHERE cp.code='MAVI-09' AND psc.sequence < 99) as m09,
  COUNT(psc.id) FILTER (WHERE cp.code='MAVI-11' AND psc.sequence < 99) as m11
FROM product_template pt
JOIN amunet_quality_parameter_product_rel ppr ON ppr.product_tmpl_id = pt.id
JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
LEFT JOIN amunet_quality_parameter_specification_config psc ON psc.product_parameter_rel_id = ppr.id
WHERE pt.default_code IN ('SPHMC34','SPHMC78','SPHMC79','SPHMC80')
  AND cp.code IN ('MAVI-04','MAVI-07','MAVI-09','MAVI-11')
GROUP BY pt.id, pt.default_code
ORDER BY pt.default_code;

COMMIT;
