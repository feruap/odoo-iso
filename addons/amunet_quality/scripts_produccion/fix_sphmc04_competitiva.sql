-- ============================================================
-- SCRIPT: SPHMC04 — configurar como prueba competitiva (igual que SPHMC10)
-- Análisis pendiente: QC/2026/00205 (ID=547)
-- Preparado: 2026-09-30 | Aplicar en amunet_prod
-- ============================================================
-- Qué hace:
--   RAÍZ (product_parameter_specification_config):
--     PASO 1: Archiva todos los OLD-118 (64 entradas) y OLD-119 (6 entradas)
--     PASO 2: Archiva MAVI-11 extras (17 de 18; conserva "Altura 6 u 8 cm")
--     PASO 3: Archiva MAVI-09 extras (4 de 6; conserva Liberación y Migración)
--     PASO 4: Actualiza MAVI-07 a criterios competitivos (iguales a SPHMC10)
--     PASO 5: Agrega MAVI-04 × 3 desde SPHMC10 (Manchas, Rasgaduras, Deformidad)
--   ANÁLISIS QC/2026/00205 (check_id=547):
--     PASO 6: Elimina 17 renglones MAVI-11 extra (queda solo "Altura 6 u 8 cm")
--     PASO 7: Elimina 14 renglones OLD-118
--     PASO 8: Inserta test_line MAVI-04 + 3 renglones detalle
-- Resultado esperado: análisis con 8 renglones (3+2+2+1)
-- ============================================================

BEGIN;

-- ============================================================
-- PASO 1: Archivar OLD-118 y OLD-119 en SPHMC04
-- ============================================================
UPDATE amunet_quality_parameter_specification_config
SET sequence = 99, write_date = NOW()
WHERE product_parameter_rel_id IN (1474, 3120, 1912)  -- OLD-118 ×2, OLD-119
  AND sequence < 99;
-- Esperado: UPDATE ~76 (64+6+6)

-- ============================================================
-- PASO 2: Archivar MAVI-11 extras (conservar solo id=72463)
-- ============================================================
UPDATE amunet_quality_parameter_specification_config
SET sequence = 99, write_date = NOW()
WHERE product_parameter_rel_id = 1603  -- MAVI-11 de SPHMC04
  AND sequence < 99
  AND id != 72463;
-- Esperado: UPDATE 17

-- ============================================================
-- PASO 3: Archivar MAVI-09 extras (conservar ids 21637 y 21638)
-- ============================================================
UPDATE amunet_quality_parameter_specification_config
SET sequence = 99, write_date = NOW()
WHERE product_parameter_rel_id = 544  -- MAVI-09 de SPHMC04
  AND sequence < 99
  AND id NOT IN (21637, 21638);
-- Esperado: UPDATE 4

-- ============================================================
-- PASO 4: Actualizar MAVI-07 a criterios competitivos (como SPHMC10)
-- ============================================================
-- Muestra positiva: solo línea control visible (igual a SPHMC10 spec_id=629)
UPDATE amunet_quality_parameter_specification_config
SET acceptance_criteria = 'Visualización sólo de la línea control patrón #5',
    write_date = NOW()
WHERE id = 78257;

-- Muestra negativa: línea control + línea de prueba visible
UPDATE amunet_quality_parameter_specification_config
SET acceptance_criteria = 'Visualización de la línea control y de la línea de prueba dentro del patrón #4 al #1',
    write_date = NOW()
WHERE id = 78322;
-- Esperado: UPDATE 1 × 2 veces

-- ============================================================
-- PASO 5: Agregar MAVI-04 × 3 desde SPHMC10
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
  3184,  -- MAVI-04 ppr de SPHMC04
  ref.specification_id, ref.sequence, ref.uom_id,
  1434, ref.parameter_id, ref.company_id,  -- tmpl_id=1434 (SPHMC04)
  ref.specification_name, ref.evaluation_type, ref.acceptance_criteria,
  ref.binary_option_pass, ref.binary_option_fail,
  ref.binary_expected_option, ref.config_summary,
  ref.min_value, ref.max_value,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_specification_config ref
JOIN amunet_quality_parameter_product_rel ref_ppr ON ref_ppr.id = ref.product_parameter_rel_id
JOIN product_template ref_pt ON ref_pt.id = ref_ppr.product_tmpl_id
JOIN amunet_quality_check_parameter cp ON cp.id = ref_ppr.parameter_id
WHERE ref_pt.default_code = 'SPHMC10'
  AND cp.code = 'MAVI-04'
  AND ref.sequence < 99
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config e
    WHERE e.product_parameter_rel_id = 3184
      AND e.specification_name = ref.specification_name
      AND e.sequence < 99
  );
-- Esperado: INSERT 0 3

-- ============================================================
-- PASO 6: Eliminar 17 renglones MAVI-11 extra del análisis
-- (conservar solo id=3209 = "Altura 6 u 8 cm")
-- ============================================================
DELETE FROM amunet_quality_test_line_detail
WHERE check_id = 547
  AND test_line_id = 1405  -- test_line MAVI-11
  AND id != 3209;
-- Esperado: DELETE 17

-- ============================================================
-- PASO 7: Eliminar 14 renglones OLD-118 del análisis
-- ============================================================
DELETE FROM amunet_quality_test_line_detail
WHERE check_id = 547
  AND id IN (3226,3227,3228,3229,3230,3231,3232,3233,3234,3235,3236,3237,3238,3239);
-- Esperado: DELETE 14

-- ============================================================
-- PASO 8: Insertar test_line MAVI-04 + 3 renglones detalle
-- ============================================================

-- test_line para MAVI-04
INSERT INTO amunet_quality_test_line (
  check_id, parameter_id, parameter_rel_id,
  name, code, sequence,
  create_uid, write_uid, create_date, write_date
)
SELECT 547, 1, 3184, 'Aspectos', 'MAVI-04', 5, 1, 1, NOW(), NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM amunet_quality_test_line
  WHERE check_id = 547 AND parameter_id = 1
);

-- Renglones detalle MAVI-04 (copia de spec_configs recién creados)
INSERT INTO amunet_quality_test_line_detail (
  test_line_id, check_id, specification_config_id, specification_id,
  name, evaluation_type, acceptance_criteria,
  binary_option_pass, binary_option_fail,
  min_value, max_value, sequence,
  create_uid, write_uid, create_date, write_date
)
SELECT
  qtl.id, 547, psc.id, psc.specification_id,
  psc.specification_name, psc.evaluation_type, psc.acceptance_criteria,
  psc.binary_option_pass, psc.binary_option_fail,
  psc.min_value, psc.max_value, psc.sequence,
  1, 1, NOW(), NOW()
FROM amunet_quality_test_line qtl
JOIN amunet_quality_parameter_specification_config psc
  ON psc.product_parameter_rel_id = qtl.parameter_rel_id
WHERE qtl.check_id = 547 AND qtl.parameter_id = 1
  AND psc.sequence < 99
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line_detail
    WHERE test_line_id = qtl.id AND specification_config_id = psc.id
  );
-- Esperado: INSERT 0 3

-- ============================================================
-- VERIFICACIÓN FINAL
-- ============================================================

-- Raíz: debe mostrar MAVI-04=3, MAVI-07=2, MAVI-09=2, MAVI-11=1
SELECT cp.code, COUNT(psc.id) FILTER (WHERE psc.sequence < 99) as activas
FROM amunet_quality_parameter_product_rel ppr
JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
LEFT JOIN amunet_quality_parameter_specification_config psc
  ON psc.product_parameter_rel_id = ppr.id
WHERE ppr.product_tmpl_id = 1434
  AND cp.code IN ('MAVI-04','MAVI-07','MAVI-09','MAVI-11')
GROUP BY cp.code ORDER BY cp.code;

-- Análisis: debe mostrar 8 renglones (3+2+2+1)
SELECT cp.code, COUNT(tld.id) as renglones
FROM amunet_quality_test_line_detail tld
JOIN amunet_quality_test_line qtl ON qtl.id = tld.test_line_id
JOIN amunet_quality_check_parameter cp ON cp.id = qtl.parameter_id
WHERE tld.check_id = 547
GROUP BY cp.code ORDER BY cp.code;

COMMIT;
