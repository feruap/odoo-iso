-- ============================================================
-- FIX ANÁLISIS 888 (QC/2026/00146 — DMPSA01 PSA semicuantitativa)
-- Solicitado por: Diana Flores (Calidad) — 2026-09-08
-- Ejecutar en la base de PRODUCCIÓN
--
-- Qué hace:
--   A) Reactiva MGA-0486 e INC-002 en la configuración del producto DMPSA01
--      (y DMTSH02, DMFRT02) si están inactivos
--   B) Actualiza el análisis QC/2026/00146:
--      - Convierte MAVI-07 → MAVI-15 (Control negativo + Control positivo)
--      - Elimina líneas VAMA
--      - Agrega detalle INC-002 y MGA-0486 si no existen en el análisis
-- ============================================================

-- ==== PARTE A: Producto — reactivar MGA-0486 e INC-002 para PSA/TSH/Ferrinet ====

-- Ver estado actual de los parámetros
SELECT pt.default_code, p.code, r.active, r.active_spec_count
FROM amunet_quality_parameter_product_rel r
JOIN amunet_quality_check_parameter p ON p.id = r.parameter_id
JOIN product_template pt ON pt.id = r.product_tmpl_id
WHERE pt.default_code IN ('DMPSA01','DMTSH02','DMFRT02')
  AND p.code IN ('MGA-0486','INC-002','MAVI-15','MAVI-04','MAVI-09')
ORDER BY pt.default_code, p.code;

-- Reactivar si están inactivos
UPDATE amunet_quality_parameter_product_rel r
SET active = true, write_date = NOW()
FROM amunet_quality_check_parameter p, product_template pt
WHERE p.id = r.parameter_id
  AND pt.id = r.product_tmpl_id
  AND pt.default_code IN ('DMPSA01','DMTSH02','DMFRT02')
  AND p.code IN ('MGA-0486','INC-002')
  AND r.active = false;

-- ==== PARTE B: Análisis QC/2026/00146 ====

-- PASO 1: Ver estado actual del análisis
SELECT d.id, d.name, d.evaluation_type, d.verdict
FROM amunet_quality_test_line_detail d
WHERE d.check_id = (SELECT id FROM amunet_quality_check WHERE name = 'QC/2026/00146')
ORDER BY d.sequence;

-- PASO 2: Convertir Control negativo (MAVI-07 → MAVI-15)
UPDATE amunet_quality_test_line_detail
SET name = 'Control negativo',
    evaluation_type = 'vama_multi_check',
    text_phrase_mapping = '{"fixed_sample_type":"negative","positions":[{"index":0,"type":"select","label":"Intensidad observada (PRS-01)","instruction":"Seleccione el nivel de la línea T respecto a la línea R.","options":[{"label":"Bajo: C+R visibles, T no visible","value":"bajo"},{"label":"Intermedio: C+R+T visibles, T≈R","value":"intermedio"},{"label":"Alto: C+T visibles, T>R","value":"alto"}]}],"phrase_template":"Control negativo: {0}","evaluation":{"rules":[{"sample_type":"negative","result":"bajo","verdict":"pass","message":"Control negativo: Bajo (T no visible) — CUMPLE"},{"sample_type":"negative","result":"intermedio","verdict":"fail","message":"Control negativo: Intermedio — NO CUMPLE"},{"sample_type":"negative","result":"alto","verdict":"fail","message":"Control negativo: Alto — NO CUMPLE"}]}}',
    verdict = NULL, verdict_message = NULL,
    multi_check_results_json = NULL, result_text_pattern = NULL,
    write_date = NOW()
WHERE check_id = (SELECT id FROM amunet_quality_check WHERE name = 'QC/2026/00146')
  AND name ILIKE '%negativ%';

-- PASO 3: Convertir Control positivo (MAVI-07 → MAVI-15 con 2 posiciones)
UPDATE amunet_quality_test_line_detail
SET name = 'Control positivo',
    evaluation_type = 'vama_multi_check',
    text_phrase_mapping = '{"fixed_sample_type":"positive","positions":[{"index":0,"type":"select","label":"Positivo bajo — intensidad de la línea T","instruction":"Seleccione el nivel de la línea T respecto a la línea R.","pass_value":"intermedio","options":[{"label":"Bajo: C+R visibles, T no visible","value":"bajo"},{"label":"Intermedio: C+R+T visibles, T≈R","value":"intermedio"},{"label":"Alto: C+T visibles, T>R","value":"alto"}]},{"index":1,"type":"select","label":"Positivo alto — intensidad de la línea T","instruction":"Seleccione el nivel de la línea T respecto a la línea R.","pass_value":"alto","options":[{"label":"Bajo: C+R visibles, T no visible","value":"bajo"},{"label":"Intermedio: C+R+T visibles, T≈R","value":"intermedio"},{"label":"Alto: C+T visibles, T>R","value":"alto"}]}],"phrase_template":"Control positivo bajo: {0} / Control positivo alto: {1}","success_message":"Control positivo: Positivo bajo=Intermedio y Positivo alto=Alto — CUMPLE","error_prefix":"Control positivo NO CUMPLE:"}',
    verdict = NULL, verdict_message = NULL,
    multi_check_results_json = NULL, result_text_pattern = NULL,
    write_date = NOW()
WHERE check_id = (SELECT id FROM amunet_quality_check WHERE name = 'QC/2026/00146')
  AND name ILIKE '%positiv%';

-- PASO 4: Eliminar líneas VAMA del análisis
DELETE FROM amunet_quality_test_line_detail
WHERE check_id = (SELECT id FROM amunet_quality_check WHERE name = 'QC/2026/00146')
  AND (name ILIKE 'VAMA%'
       OR name ILIKE '%etiqueta%'
       OR name ILIKE '%instructivo%'
       OR name ILIKE '%termosellado%'
       OR name ILIKE '%gotero%'
       OR name ILIKE '%vial%');

-- PASO 5: Agregar Hermeticidad (MGA-0486) si no existe en el análisis
INSERT INTO amunet_quality_test_line_detail
    (check_id, name, evaluation_type, acceptance_criteria,
     binary_option_pass, binary_option_fail, expected_value_binary,
     sequence, verdict, create_date, write_date, create_uid, write_uid)
SELECT
    (SELECT id FROM amunet_quality_check WHERE name = 'QC/2026/00146'),
    'Prueba de colorante',
    'binary_selection',
    'Ausencia de colorante',
    'Ausencia de colorante',
    'Presencia de colorante',
    'pass',
    5,
    NULL,
    NOW(), NOW(), 1, 1
WHERE NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line_detail
    WHERE check_id = (SELECT id FROM amunet_quality_check WHERE name = 'QC/2026/00146')
      AND name ILIKE '%colorante%'
);

-- PASO 6: Agregar INC-002 si no existe en el análisis
INSERT INTO amunet_quality_test_line_detail
    (check_id, name, evaluation_type, acceptance_criteria,
     binary_option_pass, binary_option_fail, expected_value_binary,
     sequence, verdict, create_date, write_date, create_uid, write_uid)
SELECT
    (SELECT id FROM amunet_quality_check WHERE name = 'QC/2026/00146'),
    'Verificación de contenido de empaque',
    'binary_selection',
    'El contenido coincide con el especificado en el manual.',
    'Contenido coincide',
    'Contenido no coincide',
    'pass',
    15,
    NULL,
    NOW(), NOW(), 1, 1
WHERE NOT EXISTS (
    SELECT 1 FROM amunet_quality_test_line_detail
    WHERE check_id = (SELECT id FROM amunet_quality_check WHERE name = 'QC/2026/00146')
      AND name ILIKE '%contenido%'
);

-- PASO 7: Verificación final — debe mostrar sin VAMAs, con Control negativo/positivo
-- en vama_multi_check, con Hermeticidad e INC-002
SELECT d.id, d.name, d.evaluation_type, d.verdict
FROM amunet_quality_test_line_detail d
WHERE d.check_id = (SELECT id FROM amunet_quality_check WHERE name = 'QC/2026/00146')
ORDER BY d.sequence;
