-- ============================================================
-- SCRIPT: Configurar STGEL02 — crear parámetros y puntos de control
-- Análisis: QC/2026/00510 (ID=939), lote GEL02082601
-- Referencia: RAST-047 / CERST-047 Gel refrigerante BRICK
-- Elaborado: 2026-09-29 | Rev 2: 2026-09-29 (VAMA-100 → MAVI-23)
-- Aplicar en amunet_prod
-- ============================================================
-- Qué hace:
--   PASO 0: Agrega 2 specs al catálogo de MAVI-23 para gel refrigerante
--           (Tiempo de congelación, Mantenimiento de temperatura)
--   PASO 1: Crea 3 relaciones parámetro-producto para STGEL02
--           (MAVI-04, MAVI-23, MAVI-11)
--   PASO 2: Crea 8 especificaciones de STGEL02 según CERST-047:
--           - MAVI-04 × 3: Manchas, Rasgaduras, Deformidad
--           - MAVI-23 × 2: Tiempo de congelación (<24h), Mantenimiento temp (≤20°C)
--           - MAVI-11 × 3: Largo (17±1 cm), Ancho (12±1 cm), Grosor (1.5±0.5 cm)
--   PASO 3: Crea las 3 líneas de parámetros del análisis 939
--   PASO 4: Crea los 8 renglones detalle del análisis 939
-- Script idempotente: cada INSERT tiene NOT EXISTS guard.
-- No cancela ni modifica ningún análisis existente.
-- ============================================================

BEGIN;

-- ============================================================
-- PASO 0: Agregar specs de gel al catálogo de MAVI-23
-- ============================================================

INSERT INTO amunet_quality_check_parameter_specification
  (parameter_id, name, evaluation_type, create_uid, write_uid, create_date, write_date)
SELECT 151, 'Tiempo de congelación', 'numeric_range', 1, 1, NOW(), NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM amunet_quality_check_parameter_specification
  WHERE parameter_id = 151 AND name = 'Tiempo de congelación'
);

INSERT INTO amunet_quality_check_parameter_specification
  (parameter_id, name, evaluation_type, create_uid, write_uid, create_date, write_date)
SELECT 151, 'Mantenimiento de temperatura', 'numeric_range', 1, 1, NOW(), NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM amunet_quality_check_parameter_specification
  WHERE parameter_id = 151 AND name = 'Mantenimiento de temperatura'
);
-- Esperado: INSERT 0 1 × 2 veces

-- ============================================================
-- PASO 1: Crear relaciones parámetro-producto para STGEL02
-- ============================================================

-- MAVI-04 (Aspectos / empaque)
INSERT INTO amunet_quality_parameter_product_rel
  (product_tmpl_id, parameter_id, active, create_uid, write_uid, create_date, write_date)
SELECT 2311, 1, TRUE, 1, 1, NOW(), NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM amunet_quality_parameter_product_rel
  WHERE product_tmpl_id = 2311 AND parameter_id = 1
);

-- MAVI-23 (Funcionalidad del gel refrigerante)
INSERT INTO amunet_quality_parameter_product_rel
  (product_tmpl_id, parameter_id, active, create_uid, write_uid, create_date, write_date)
SELECT 2311, 151, TRUE, 1, 1, NOW(), NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM amunet_quality_parameter_product_rel
  WHERE product_tmpl_id = 2311 AND parameter_id = 151
);

-- MAVI-11 (Dimensiones)
INSERT INTO amunet_quality_parameter_product_rel
  (product_tmpl_id, parameter_id, active, create_uid, write_uid, create_date, write_date)
SELECT 2311, 64, TRUE, 1, 1, NOW(), NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM amunet_quality_parameter_product_rel
  WHERE product_tmpl_id = 2311 AND parameter_id = 64
);
-- Esperado: INSERT 0 1 × 3 veces (o 0 si ya existían)

-- ============================================================
-- PASO 2: Crear especificaciones de STGEL02
-- ============================================================

-- ---- MAVI-04: Manchas y/o suciedad (spec_id=120) ----
INSERT INTO amunet_quality_parameter_specification_config (
  product_parameter_rel_id, specification_id, sequence,
  product_tmpl_id, parameter_id,
  specification_name, evaluation_type, acceptance_criteria,
  binary_option_pass, binary_option_fail, binary_expected_option,
  min_value, max_value,
  create_uid, write_uid, create_date, write_date
)
SELECT
  ppr.id, 120, 10,
  2311, 1,
  'Manchas y/o suciedad', 'binary_selection', 'Sin manchas y/o suciedad',
  'Sin manchas y/o suciedad', 'Con manchas y/o suciedad', 'pass',
  0, 0,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel ppr
WHERE ppr.product_tmpl_id = 2311 AND ppr.parameter_id = 1
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config
    WHERE product_parameter_rel_id = ppr.id
      AND specification_name = 'Manchas y/o suciedad' AND sequence < 99
  );

-- ---- MAVI-04: Rasgaduras (spec_id=121) ----
INSERT INTO amunet_quality_parameter_specification_config (
  product_parameter_rel_id, specification_id, sequence,
  product_tmpl_id, parameter_id,
  specification_name, evaluation_type, acceptance_criteria,
  binary_option_pass, binary_option_fail, binary_expected_option,
  min_value, max_value,
  create_uid, write_uid, create_date, write_date
)
SELECT
  ppr.id, 121, 20,
  2311, 1,
  'Rasgaduras', 'binary_selection', 'Sin rasgaduras',
  'Sin rasgaduras', 'Con rasgaduras', 'pass',
  0, 0,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel ppr
WHERE ppr.product_tmpl_id = 2311 AND ppr.parameter_id = 1
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config
    WHERE product_parameter_rel_id = ppr.id
      AND specification_name = 'Rasgaduras' AND sequence < 99
  );

-- ---- MAVI-04: Deformidad o deterioro (spec_id=348) ----
INSERT INTO amunet_quality_parameter_specification_config (
  product_parameter_rel_id, specification_id, sequence,
  product_tmpl_id, parameter_id,
  specification_name, evaluation_type, acceptance_criteria,
  binary_option_pass, binary_option_fail, binary_expected_option,
  min_value, max_value,
  create_uid, write_uid, create_date, write_date
)
SELECT
  ppr.id, 348, 30,
  2311, 1,
  'Deformidad o deterioro', 'binary_selection', 'Sin deformidad o deterioro',
  'Sin deformidad o deterioro', 'Con deformidad o deterioro', 'pass',
  0, 0,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel ppr
WHERE ppr.product_tmpl_id = 2311 AND ppr.parameter_id = 1
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config
    WHERE product_parameter_rel_id = ppr.id
      AND specification_name = 'Deformidad o deterioro' AND sequence < 99
  );

-- ---- MAVI-23: Tiempo de congelación (<24h) ----
INSERT INTO amunet_quality_parameter_specification_config (
  product_parameter_rel_id, specification_id, sequence,
  product_tmpl_id, parameter_id,
  specification_name, evaluation_type, acceptance_criteria,
  min_value, max_value,
  create_uid, write_uid, create_date, write_date
)
SELECT
  ppr.id,
  (SELECT id FROM amunet_quality_check_parameter_specification
   WHERE parameter_id = 151 AND name = 'Tiempo de congelación'),
  10,
  2311, 151,
  'Tiempo de congelación', 'numeric_range', 'Menos de 24 horas',
  0, 24,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel ppr
WHERE ppr.product_tmpl_id = 2311 AND ppr.parameter_id = 151
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config
    WHERE product_parameter_rel_id = ppr.id
      AND specification_name = 'Tiempo de congelación' AND sequence < 99
  );

-- ---- MAVI-23: Mantenimiento de temperatura (≤20°C 8h) ----
INSERT INTO amunet_quality_parameter_specification_config (
  product_parameter_rel_id, specification_id, sequence,
  product_tmpl_id, parameter_id,
  specification_name, evaluation_type, acceptance_criteria,
  min_value, max_value,
  create_uid, write_uid, create_date, write_date
)
SELECT
  ppr.id,
  (SELECT id FROM amunet_quality_check_parameter_specification
   WHERE parameter_id = 151 AND name = 'Mantenimiento de temperatura'),
  20,
  2311, 151,
  'Mantenimiento de temperatura', 'numeric_range',
  'Mantiene temperatura ≤20°C ± 2°C durante al menos 8 horas',
  -30, 20,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel ppr
WHERE ppr.product_tmpl_id = 2311 AND ppr.parameter_id = 151
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config
    WHERE product_parameter_rel_id = ppr.id
      AND specification_name = 'Mantenimiento de temperatura' AND sequence < 99
  );

-- ---- MAVI-11: Largo (spec_id=380, 17±1 cm = 16-18) ----
INSERT INTO amunet_quality_parameter_specification_config (
  product_parameter_rel_id, specification_id, sequence,
  product_tmpl_id, parameter_id,
  specification_name, evaluation_type, acceptance_criteria,
  min_value, max_value,
  create_uid, write_uid, create_date, write_date
)
SELECT
  ppr.id, 380, 10,
  2311, 64,
  'Largo', 'numeric_range', '17 ± 1 cm',
  16, 18,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel ppr
WHERE ppr.product_tmpl_id = 2311 AND ppr.parameter_id = 64
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config
    WHERE product_parameter_rel_id = ppr.id
      AND specification_name = 'Largo' AND sequence < 99
  );

-- ---- MAVI-11: Ancho (spec_id=379, 12±1 cm = 11-13) ----
INSERT INTO amunet_quality_parameter_specification_config (
  product_parameter_rel_id, specification_id, sequence,
  product_tmpl_id, parameter_id,
  specification_name, evaluation_type, acceptance_criteria,
  min_value, max_value,
  create_uid, write_uid, create_date, write_date
)
SELECT
  ppr.id, 379, 20,
  2311, 64,
  'Ancho', 'numeric_range', '12 ± 1 cm',
  11, 13,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel ppr
WHERE ppr.product_tmpl_id = 2311 AND ppr.parameter_id = 64
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config
    WHERE product_parameter_rel_id = ppr.id
      AND specification_name = 'Ancho' AND sequence < 99
  );

-- ---- MAVI-11: Grosor (spec_id=381, 1.5±0.5 cm = 1.0-2.0) ----
INSERT INTO amunet_quality_parameter_specification_config (
  product_parameter_rel_id, specification_id, sequence,
  product_tmpl_id, parameter_id,
  specification_name, evaluation_type, acceptance_criteria,
  min_value, max_value,
  create_uid, write_uid, create_date, write_date
)
SELECT
  ppr.id, 381, 30,
  2311, 64,
  'Grosor', 'numeric_range', '1.5 ± 0.5 cm',
  1.0, 2.0,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel ppr
WHERE ppr.product_tmpl_id = 2311 AND ppr.parameter_id = 64
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config
    WHERE product_parameter_rel_id = ppr.id
      AND specification_name = 'Grosor' AND sequence < 99
  );
-- Esperado: INSERT 0 1 × 8 veces

-- ============================================================
-- PASO 3: Crear líneas de parámetros para el análisis 939
-- ============================================================

-- MAVI-04 line
INSERT INTO amunet_quality_test_line (
  check_id, parameter_id, parameter_rel_id,
  name, code, sequence,
  create_uid, write_uid, create_date, write_date
)
SELECT
  939, 1, ppr.id,
  'Aspectos', 'MAVI-04', 10,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel ppr
WHERE ppr.product_tmpl_id = 2311 AND ppr.parameter_id = 1
  AND EXISTS (SELECT 1 FROM amunet_quality_check WHERE id = 939)
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line
    WHERE check_id = 939 AND parameter_id = 1
  );

-- MAVI-23 line
INSERT INTO amunet_quality_test_line (
  check_id, parameter_id, parameter_rel_id,
  name, code, sequence,
  create_uid, write_uid, create_date, write_date
)
SELECT
  939, 151, ppr.id,
  'Determinación de funcionalidad del gel refrigerante', 'MAVI-23', 20,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel ppr
WHERE ppr.product_tmpl_id = 2311 AND ppr.parameter_id = 151
  AND EXISTS (SELECT 1 FROM amunet_quality_check WHERE id = 939)
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line
    WHERE check_id = 939 AND parameter_id = 151
  );

-- MAVI-11 line
INSERT INTO amunet_quality_test_line (
  check_id, parameter_id, parameter_rel_id,
  name, code, sequence,
  create_uid, write_uid, create_date, write_date
)
SELECT
  939, 64, ppr.id,
  'Longitud y/o grosor', 'MAVI-11', 30,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel ppr
WHERE ppr.product_tmpl_id = 2311 AND ppr.parameter_id = 64
  AND EXISTS (SELECT 1 FROM amunet_quality_check WHERE id = 939)
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line
    WHERE check_id = 939 AND parameter_id = 64
  );
-- Esperado: INSERT 0 1 × 3 veces

-- ============================================================
-- PASO 4: Crear renglones detalle del análisis 939
-- ============================================================

-- ---- MAVI-04: Manchas y/o suciedad ----
INSERT INTO amunet_quality_test_line_detail (
  test_line_id, check_id, specification_config_id, specification_id,
  name, evaluation_type, acceptance_criteria,
  binary_option_pass, binary_option_fail,
  min_value, max_value, sequence,
  create_uid, write_uid, create_date, write_date
)
SELECT
  qtl.id, 939, psc.id, psc.specification_id,
  psc.specification_name, psc.evaluation_type, psc.acceptance_criteria,
  psc.binary_option_pass, psc.binary_option_fail,
  psc.min_value, psc.max_value, psc.sequence,
  1, 1, NOW(), NOW()
FROM amunet_quality_test_line qtl
JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = qtl.parameter_rel_id
JOIN amunet_quality_parameter_specification_config psc ON psc.product_parameter_rel_id = ppr.id
WHERE qtl.check_id = 939 AND qtl.parameter_id = 1
  AND psc.specification_name = 'Manchas y/o suciedad' AND psc.sequence < 99
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line_detail
    WHERE test_line_id = qtl.id AND specification_config_id = psc.id
  );

-- ---- MAVI-04: Rasgaduras ----
INSERT INTO amunet_quality_test_line_detail (
  test_line_id, check_id, specification_config_id, specification_id,
  name, evaluation_type, acceptance_criteria,
  binary_option_pass, binary_option_fail,
  min_value, max_value, sequence,
  create_uid, write_uid, create_date, write_date
)
SELECT
  qtl.id, 939, psc.id, psc.specification_id,
  psc.specification_name, psc.evaluation_type, psc.acceptance_criteria,
  psc.binary_option_pass, psc.binary_option_fail,
  psc.min_value, psc.max_value, psc.sequence,
  1, 1, NOW(), NOW()
FROM amunet_quality_test_line qtl
JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = qtl.parameter_rel_id
JOIN amunet_quality_parameter_specification_config psc ON psc.product_parameter_rel_id = ppr.id
WHERE qtl.check_id = 939 AND qtl.parameter_id = 1
  AND psc.specification_name = 'Rasgaduras' AND psc.sequence < 99
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line_detail
    WHERE test_line_id = qtl.id AND specification_config_id = psc.id
  );

-- ---- MAVI-04: Deformidad o deterioro ----
INSERT INTO amunet_quality_test_line_detail (
  test_line_id, check_id, specification_config_id, specification_id,
  name, evaluation_type, acceptance_criteria,
  binary_option_pass, binary_option_fail,
  min_value, max_value, sequence,
  create_uid, write_uid, create_date, write_date
)
SELECT
  qtl.id, 939, psc.id, psc.specification_id,
  psc.specification_name, psc.evaluation_type, psc.acceptance_criteria,
  psc.binary_option_pass, psc.binary_option_fail,
  psc.min_value, psc.max_value, psc.sequence,
  1, 1, NOW(), NOW()
FROM amunet_quality_test_line qtl
JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = qtl.parameter_rel_id
JOIN amunet_quality_parameter_specification_config psc ON psc.product_parameter_rel_id = ppr.id
WHERE qtl.check_id = 939 AND qtl.parameter_id = 1
  AND psc.specification_name = 'Deformidad o deterioro' AND psc.sequence < 99
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line_detail
    WHERE test_line_id = qtl.id AND specification_config_id = psc.id
  );

-- ---- MAVI-23: Tiempo de congelación ----
INSERT INTO amunet_quality_test_line_detail (
  test_line_id, check_id, specification_config_id, specification_id,
  name, evaluation_type, acceptance_criteria,
  min_value, max_value, sequence,
  create_uid, write_uid, create_date, write_date
)
SELECT
  qtl.id, 939, psc.id, psc.specification_id,
  psc.specification_name, psc.evaluation_type, psc.acceptance_criteria,
  psc.min_value, psc.max_value, psc.sequence,
  1, 1, NOW(), NOW()
FROM amunet_quality_test_line qtl
JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = qtl.parameter_rel_id
JOIN amunet_quality_parameter_specification_config psc ON psc.product_parameter_rel_id = ppr.id
WHERE qtl.check_id = 939 AND qtl.parameter_id = 151
  AND psc.specification_name = 'Tiempo de congelación' AND psc.sequence < 99
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line_detail
    WHERE test_line_id = qtl.id AND specification_config_id = psc.id
  );

-- ---- MAVI-23: Mantenimiento de temperatura ----
INSERT INTO amunet_quality_test_line_detail (
  test_line_id, check_id, specification_config_id, specification_id,
  name, evaluation_type, acceptance_criteria,
  min_value, max_value, sequence,
  create_uid, write_uid, create_date, write_date
)
SELECT
  qtl.id, 939, psc.id, psc.specification_id,
  psc.specification_name, psc.evaluation_type, psc.acceptance_criteria,
  psc.min_value, psc.max_value, psc.sequence,
  1, 1, NOW(), NOW()
FROM amunet_quality_test_line qtl
JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = qtl.parameter_rel_id
JOIN amunet_quality_parameter_specification_config psc ON psc.product_parameter_rel_id = ppr.id
WHERE qtl.check_id = 939 AND qtl.parameter_id = 151
  AND psc.specification_name = 'Mantenimiento de temperatura' AND psc.sequence < 99
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line_detail
    WHERE test_line_id = qtl.id AND specification_config_id = psc.id
  );

-- ---- MAVI-11: Largo ----
INSERT INTO amunet_quality_test_line_detail (
  test_line_id, check_id, specification_config_id, specification_id,
  name, evaluation_type, acceptance_criteria,
  min_value, max_value, sequence,
  create_uid, write_uid, create_date, write_date
)
SELECT
  qtl.id, 939, psc.id, psc.specification_id,
  psc.specification_name, psc.evaluation_type, psc.acceptance_criteria,
  psc.min_value, psc.max_value, psc.sequence,
  1, 1, NOW(), NOW()
FROM amunet_quality_test_line qtl
JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = qtl.parameter_rel_id
JOIN amunet_quality_parameter_specification_config psc ON psc.product_parameter_rel_id = ppr.id
WHERE qtl.check_id = 939 AND qtl.parameter_id = 64
  AND psc.specification_name = 'Largo' AND psc.sequence < 99
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line_detail
    WHERE test_line_id = qtl.id AND specification_config_id = psc.id
  );

-- ---- MAVI-11: Ancho ----
INSERT INTO amunet_quality_test_line_detail (
  test_line_id, check_id, specification_config_id, specification_id,
  name, evaluation_type, acceptance_criteria,
  min_value, max_value, sequence,
  create_uid, write_uid, create_date, write_date
)
SELECT
  qtl.id, 939, psc.id, psc.specification_id,
  psc.specification_name, psc.evaluation_type, psc.acceptance_criteria,
  psc.min_value, psc.max_value, psc.sequence,
  1, 1, NOW(), NOW()
FROM amunet_quality_test_line qtl
JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = qtl.parameter_rel_id
JOIN amunet_quality_parameter_specification_config psc ON psc.product_parameter_rel_id = ppr.id
WHERE qtl.check_id = 939 AND qtl.parameter_id = 64
  AND psc.specification_name = 'Ancho' AND psc.sequence < 99
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line_detail
    WHERE test_line_id = qtl.id AND specification_config_id = psc.id
  );

-- ---- MAVI-11: Grosor ----
INSERT INTO amunet_quality_test_line_detail (
  test_line_id, check_id, specification_config_id, specification_id,
  name, evaluation_type, acceptance_criteria,
  min_value, max_value, sequence,
  create_uid, write_uid, create_date, write_date
)
SELECT
  qtl.id, 939, psc.id, psc.specification_id,
  psc.specification_name, psc.evaluation_type, psc.acceptance_criteria,
  psc.min_value, psc.max_value, psc.sequence,
  1, 1, NOW(), NOW()
FROM amunet_quality_test_line qtl
JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = qtl.parameter_rel_id
JOIN amunet_quality_parameter_specification_config psc ON psc.product_parameter_rel_id = ppr.id
WHERE qtl.check_id = 939 AND qtl.parameter_id = 64
  AND psc.specification_name = 'Grosor' AND psc.sequence < 99
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line_detail
    WHERE test_line_id = qtl.id AND specification_config_id = psc.id
  );
-- Esperado: INSERT 0 1 × 8 veces

-- ============================================================
-- VERIFICACIÓN FINAL
-- ============================================================

-- Debe mostrar 8 renglones para el análisis 939
SELECT
  cp.code as param, psc.specification_name as especificacion,
  psc.evaluation_type as tipo, psc.acceptance_criteria as criterio,
  psc.min_value as min, psc.max_value as max
FROM amunet_quality_test_line_detail tld
JOIN amunet_quality_test_line qtl ON qtl.id = tld.test_line_id
JOIN amunet_quality_check_parameter cp ON cp.id = qtl.parameter_id
JOIN amunet_quality_parameter_specification_config psc ON psc.id = tld.specification_config_id
WHERE tld.check_id = 939
ORDER BY qtl.sequence, psc.sequence;

-- Configuración raíz de STGEL02 (debe mostrar MAVI-04=3, MAVI-23=2, MAVI-11=3)
SELECT cp.code, COUNT(psc.id) as specs_activas
FROM amunet_quality_parameter_product_rel ppr
JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
LEFT JOIN amunet_quality_parameter_specification_config psc
  ON psc.product_parameter_rel_id = ppr.id AND psc.sequence < 99
WHERE ppr.product_tmpl_id = 2311
GROUP BY cp.code ORDER BY cp.code;

COMMIT;
