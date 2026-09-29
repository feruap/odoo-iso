-- ============================================================
-- SCRIPT DE CORRECCIÓN v4: SPHMC85-88 CM — Limpieza de spec_configs
-- Preparado: 2026-09-29
-- Ejecutar SOLO en amunet_prod, por Fernando/desarrollo
-- ============================================================
-- IMPACTO: Los análisis QC/2026/00503 (SPHMC86 in_progress),
-- QC/2026/00504 (SPHMC87 in_progress) y QC/2026/00505 (SPHMC88 draft)
-- serán cancelados. Diana puede volver a llenarlos después de la corrección.
-- ============================================================

BEGIN;

-- ============================================================
-- PASO 1: Cancelar los análisis en proceso / borrador de los CM
-- (usando folio para evitar depender de IDs entre ambientes)
-- ============================================================
UPDATE amunet_quality_check
SET state = 'cancel', write_date = NOW()
WHERE name IN ('QC/2026/00503', 'QC/2026/00504', 'QC/2026/00505')
  AND state IN ('in_progress', 'draft', 'confirm');

-- ============================================================
-- PASO 2: Borrar test_line_detail que referencian spec_configs malos
-- ============================================================

-- a) Líneas que apuntan a MAVI-04 extras (no son Manchas/Rasgaduras/Deformidad)
DELETE FROM amunet_quality_test_line_detail
WHERE specification_config_id IN (
  SELECT psc.id
  FROM amunet_quality_parameter_specification_config psc
  JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = psc.product_parameter_rel_id
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code IN ('SPHMC85','SPHMC86','SPHMC87','SPHMC88')
    AND cp.code = 'MAVI-04'
    AND psc.specification_name NOT IN (
        'Manchas y/o suciedad', 'Rasgaduras', 'Deformidad o deterioro'
    )
);

-- b) Líneas que apuntan a MAVI-09 con placeholder XX o sin rango real
DELETE FROM amunet_quality_test_line_detail
WHERE specification_config_id IN (
  SELECT psc.id
  FROM amunet_quality_parameter_specification_config psc
  JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = psc.product_parameter_rel_id
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code IN ('SPHMC85','SPHMC86','SPHMC87','SPHMC88')
    AND cp.code = 'MAVI-09'
    AND (
      psc.acceptance_criteria LIKE '%XX%'
      OR psc.acceptance_criteria IS NULL
      OR psc.acceptance_criteria = ''
      OR (psc.min_value = 0 AND psc.max_value = 0 AND psc.sequence < 99)
    )
);

-- ============================================================
-- PASO 3: Borrar spec_configs extras/malos
-- ============================================================

-- a) MAVI-04: entradas cuyo nombre no corresponde a los 3 ítems estándar de aspecto
DELETE FROM amunet_quality_parameter_specification_config
WHERE id IN (
  SELECT psc.id
  FROM amunet_quality_parameter_specification_config psc
  JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = psc.product_parameter_rel_id
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code IN ('SPHMC85','SPHMC86','SPHMC87','SPHMC88')
    AND cp.code = 'MAVI-04'
    AND psc.specification_name NOT IN (
        'Manchas y/o suciedad', 'Rasgaduras', 'Deformidad o deterioro'
    )
);

-- b) MAVI-09: entradas con placeholder XX o criterio vacío/sin rango
DELETE FROM amunet_quality_parameter_specification_config
WHERE id IN (
  SELECT psc.id
  FROM amunet_quality_parameter_specification_config psc
  JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = psc.product_parameter_rel_id
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code IN ('SPHMC85','SPHMC86','SPHMC87','SPHMC88')
    AND cp.code = 'MAVI-09'
    AND (
      psc.acceptance_criteria LIKE '%XX%'
      OR psc.acceptance_criteria IS NULL
      OR psc.acceptance_criteria = ''
      OR (psc.min_value = 0 AND psc.max_value = 0 AND psc.sequence < 99)
    )
);

-- ============================================================
-- PASO 4: Corregir tipo de evaluación MAVI-11 de SPHMC85
-- (tenía 'mavi_11_height', debe ser 'conditional_numeric_range')
-- Solo aplica si el tipo incorrecto existe (idempotente)
-- ============================================================
UPDATE amunet_quality_parameter_specification_config
SET evaluation_type = 'conditional_numeric_range',
    write_date = NOW()
WHERE product_parameter_rel_id IN (
  SELECT ppr.id
  FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC85' AND cp.code = 'MAVI-11'
)
AND evaluation_type = 'mavi_11_height';

-- ============================================================
-- PASO 5: Agregar entradas MAVI-04 seq-10 a SPHMC85-88
-- (les faltaban completamente — solo tenían seq-99 / formato viejo)
-- Copia de SPHMC62 (referencia), idempotente por specification_name
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
-- Para cada ref, cruzar con los 4 productos destino buscando su PPR para MAVI-04
JOIN amunet_quality_parameter_product_rel new_ppr
  ON new_ppr.parameter_id = ref_ppr.parameter_id
JOIN product_template new_pt ON new_pt.id = new_ppr.product_tmpl_id
WHERE ref_pt.default_code = 'SPHMC62'
  AND cp.code = 'MAVI-04'
  AND ref.sequence < 99
  AND new_pt.default_code IN ('SPHMC85', 'SPHMC86', 'SPHMC87', 'SPHMC88')
  -- Idempotente: no insertar si ya existe una entrada seq-10 con ese nombre
  AND NOT EXISTS (
    SELECT 1
    FROM amunet_quality_parameter_specification_config existing
    WHERE existing.product_parameter_rel_id = new_ppr.id
      AND existing.specification_name = ref.specification_name
      AND existing.sequence < 99
  );
-- Resultado esperado: INSERT 0 12

-- ============================================================
-- PASO 6: Corregir valores de SPHMC85
-- MAVI-09: textos correctos para tiempos
-- MAVI-11: criterio de aceptación
-- MAVI-04 seq-99: opciones binarias correctas (para los históricos)
-- ============================================================

-- MAVI-09 Tiempo de liberación
UPDATE amunet_quality_parameter_specification_config
SET acceptance_criteria = '1 a 30 segundos',
    binary_option_pass  = 'Captura [    ] segundos',
    binary_option_fail  = 'No captura [    ] segundos',
    min_value = 1, max_value = 30,
    write_date = NOW()
WHERE product_parameter_rel_id = (
  SELECT ppr.id
  FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC85' AND cp.code = 'MAVI-09'
)
AND specification_name = 'Tiempo de liberación'
AND sequence < 99;

-- MAVI-09 Tiempo de migración
UPDATE amunet_quality_parameter_specification_config
SET acceptance_criteria = '30 a 180 segundos',
    binary_option_pass  = 'Captura [    ] segundos',
    binary_option_fail  = 'No captura [    ] segundos',
    min_value = 30, max_value = 180,
    write_date = NOW()
WHERE product_parameter_rel_id = (
  SELECT ppr.id
  FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC85' AND cp.code = 'MAVI-09'
)
AND specification_name = 'Tiempo de migración'
AND sequence < 99;

-- MAVI-11 criterio de aceptación
UPDATE amunet_quality_parameter_specification_config
SET acceptance_criteria = 'Altura 6 u 8 cm (según aplique)',
    write_date = NOW()
WHERE product_parameter_rel_id = (
  SELECT ppr.id
  FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC85' AND cp.code = 'MAVI-11'
)
AND (acceptance_criteria IS NULL OR acceptance_criteria = '');

-- MAVI-04 seq-99: corregir opciones binarias (por si aún tienen formato viejo)
UPDATE amunet_quality_parameter_specification_config
SET binary_option_pass = 'Sin Rasgaduras',
    binary_option_fail = 'Con Rasgaduras',
    write_date = NOW()
WHERE product_parameter_rel_id = (
  SELECT ppr.id
  FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC85' AND cp.code = 'MAVI-04'
)
AND specification_name = 'Rasgaduras'
AND (binary_option_pass NOT LIKE 'Sin Rasgaduras%' OR binary_option_pass IS NULL);

UPDATE amunet_quality_parameter_specification_config
SET binary_option_pass = 'Sin Manchas y/o suciedad',
    binary_option_fail = 'Con Manchas y/o suciedad',
    write_date = NOW()
WHERE product_parameter_rel_id = (
  SELECT ppr.id
  FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC85' AND cp.code = 'MAVI-04'
)
AND specification_name = 'Manchas y/o suciedad'
AND (binary_option_pass NOT LIKE 'Sin Manchas%' OR binary_option_pass IS NULL);

UPDATE amunet_quality_parameter_specification_config
SET acceptance_criteria = 'Sin deformidad o deterioro',
    binary_option_pass  = 'Sin Deformidad o deterioro.',
    binary_option_fail  = 'Con Deformidad o deterioro.',
    write_date = NOW()
WHERE product_parameter_rel_id = (
  SELECT ppr.id
  FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE pt.default_code = 'SPHMC85' AND cp.code = 'MAVI-04'
)
AND specification_name = 'Deformidad o deterioro'
AND (binary_option_pass NOT LIKE 'Sin Deformidad%' OR binary_option_pass IS NULL);

-- ============================================================
-- VERIFICACIÓN FINAL — ejecutar antes del COMMIT para revisar
-- Resultado esperado:
--   MAVI-04 seq<99: 3 entradas por producto (Manchas, Rasgaduras, Deformidad)
--   MAVI-07 seq<99: 2 entradas por producto (neg + pos)
--   MAVI-09 seq<99: 2 entradas por producto (liberación + migración)
--   MAVI-11 seq<99: 1 entrada por producto (Altura 6 u 8 cm)
-- ============================================================
SELECT pt.default_code, cp.code as param,
       COUNT(psc.id) FILTER (WHERE psc.sequence < 99) as entradas_activas,
       COUNT(psc.id) FILTER (WHERE psc.sequence >= 99) as entradas_historico
FROM amunet_quality_parameter_specification_config psc
JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = psc.product_parameter_rel_id
JOIN product_template pt ON pt.id = ppr.product_tmpl_id
JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
WHERE pt.default_code IN ('SPHMC85','SPHMC86','SPHMC87','SPHMC88')
  AND cp.code IN ('MAVI-04','MAVI-07','MAVI-09','MAVI-11')
GROUP BY pt.default_code, cp.code
ORDER BY pt.default_code, cp.code;

COMMIT;

-- ============================================================
-- PENDIENTES ADICIONALES (aplicar en la misma sesión):
-- ============================================================
-- SPHMT07-12 puntos de control (ya aplicado en staging):
-- INSERT INTO amunet_quality_point_product_product_rel
--   (amunet_quality_point_id, product_product_id) VALUES
--   (160, 2151),(320, 2152),(121, 2153),(247, 2154),(248, 2155),(294, 2156)
-- ON CONFLICT DO NOTHING;
--
-- SPHMT03-05 puntos de control:
-- INSERT INTO amunet_quality_point_product_product_rel
--   (amunet_quality_point_id, product_product_id) VALUES
--   (308, 2201),(309, 2202),(310, 2203)
-- ON CONFLICT DO NOTHING;
