-- ============================================================
-- SCRIPT DE CORRECCIÓN: SPHMC85-88 CM — Limpieza de spec_configs
-- Preparado: 2026-09-28
-- Ejecutar SOLO en amunet_prod, por Fernando/desarrollo
-- ============================================================
-- IMPACTO: Los análisis QC/2026/00503 (SPHMC86 in_progress),
-- QC/2026/00504 (SPHMC87 in_progress) y QC/2026/00505 (SPHMC88 draft)
-- serán cancelados. Diana debe guardar o anotar cualquier dato
-- parcial de esos análisis ANTES de aplicar este script.
-- ============================================================

BEGIN;

-- PASO 1: Cancelar los análisis en proceso / borrador de los CM
-- (necesario para liberar las FK antes de borrar spec_configs)
UPDATE amunet_quality_check
SET state = 'cancel', write_date = NOW()
WHERE id IN (932, 933, 934);

-- PASO 2: Borrar las líneas de detalle de esos análisis cancelados
-- que referencian los spec_configs que vamos a eliminar
DELETE FROM amunet_quality_test_line_detail
WHERE specification_config_id IN (
  -- SPHMC85 extras (MAVI-04: Letra, Sellado, Letra adecuada; MAVI-09 dups; Vial-Altura)
  86832, 86833, 86835, 86861, 86862, 86943,
  -- SPHMC86 extras
  86964, 86965, 86967, 86993, 86994, 87075,
  -- SPHMC87 extras
  87096, 87097, 87099, 87125, 87126, 87207,
  -- SPHMC88 extras
  87228, 87229, 87231, 87257, 87258, 87339
);

-- PASO 3: Borrar los spec_configs extras
DELETE FROM amunet_quality_parameter_specification_config
WHERE id IN (
  -- SPHMC85
  86832, 86833, 86835, 86861, 86862, 86943,
  -- SPHMC86
  86964, 86965, 86967, 86993, 86994, 87075,
  -- SPHMC87
  87096, 87097, 87099, 87125, 87126, 87207,
  -- SPHMC88
  87228, 87229, 87231, 87257, 87258, 87339
);

-- PASO 4: Corregir tipo de evaluación MAVI-11 de SPHMC85
-- (86896 tenía mavi_11_height, debe ser conditional_numeric_range)
UPDATE amunet_quality_parameter_specification_config
SET evaluation_type = 'conditional_numeric_range'
WHERE id = 86896;

-- VERIFICACIÓN RÁPIDA (no debe mostrar filas extra)
SELECT pt.default_code, cp.code as param, COUNT(psc.id) as num_entradas
FROM amunet_quality_parameter_specification_config psc
JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = psc.product_parameter_rel_id
JOIN product_template pt ON pt.id = ppr.product_tmpl_id
JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
WHERE pt.default_code IN ('SPHMC85','SPHMC86','SPHMC87','SPHMC88')
  AND cp.code IN ('MAVI-04','MAVI-07','MAVI-09','MAVI-11')
GROUP BY pt.default_code, cp.code
ORDER BY pt.default_code, cp.code;
-- Resultado esperado: MAVI-04=4(1 dup irremovible), MAVI-07=2, MAVI-09=2, MAVI-11=1

COMMIT;

-- ============================================================
-- PENDIENTES ADICIONALES (aplicar en la misma ventana):
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
