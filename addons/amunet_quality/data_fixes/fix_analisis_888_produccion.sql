-- ============================================================
-- FIX ANÁLISIS 888 (QC/2026/00146 — DMPSA01 PSA semicuantitativa)
-- Solicitado por: Diana Flores (Calidad)
-- Fecha: 2026-09-08
-- Ejecutar en la base de PRODUCCIÓN
-- ============================================================

-- PASO 1: Verificar qué hay ahorita (compartir resultado con Diana antes de continuar)
SELECT d.id, d.name, d.evaluation_type, d.verdict
FROM amunet_quality_test_line_detail d
WHERE d.check_id = (SELECT id FROM amunet_quality_check WHERE name = 'QC/2026/00146')
ORDER BY d.sequence;

-- PASO 2: Convertir Control negativo (MAVI-07 → MAVI-15)
UPDATE amunet_quality_test_line_detail
SET name = 'Control negativo',
    evaluation_type = 'vama_multi_check',
    text_phrase_mapping = '{"fixed_sample_type":"negative","positions":[{"index":0,"type":"select","label":"Intensidad observada (PRS-01)","instruction":"Seleccione el nivel de la línea T respecto a la línea R.","options":[{"label":"Bajo: C+R visibles, T no visible","value":"bajo"},{"label":"Intermedio: C+R+T visibles, T≈R","value":"intermedio"},{"label":"Alto: C+T visibles, T>R","value":"alto"}]}],"phrase_template":"Control negativo: {0}","evaluation":{"rules":[{"sample_type":"negative","result":"bajo","verdict":"pass","message":"Control negativo: Bajo (T no visible) — CUMPLE"},{"sample_type":"negative","result":"intermedio","verdict":"fail","message":"Control negativo: Intermedio — NO CUMPLE"},{"sample_type":"negative","result":"alto","verdict":"fail","message":"Control negativo: Alto — NO CUMPLE"}]}}',
    verdict = NULL,
    verdict_message = NULL,
    multi_check_results_json = NULL,
    result_text_pattern = NULL,
    write_date = NOW()
WHERE check_id = (SELECT id FROM amunet_quality_check WHERE name = 'QC/2026/00146')
  AND name ILIKE '%negativ%';

-- PASO 3: Convertir Control positivo (MAVI-07 → MAVI-15 con 2 posiciones)
UPDATE amunet_quality_test_line_detail
SET name = 'Control positivo',
    evaluation_type = 'vama_multi_check',
    text_phrase_mapping = '{"fixed_sample_type":"positive","positions":[{"index":0,"type":"select","label":"Positivo bajo — intensidad de la línea T","instruction":"Seleccione el nivel de la línea T respecto a la línea R.","pass_value":"intermedio","options":[{"label":"Bajo: C+R visibles, T no visible","value":"bajo"},{"label":"Intermedio: C+R+T visibles, T≈R","value":"intermedio"},{"label":"Alto: C+T visibles, T>R","value":"alto"}]},{"index":1,"type":"select","label":"Positivo alto — intensidad de la línea T","instruction":"Seleccione el nivel de la línea T respecto a la línea R.","pass_value":"alto","options":[{"label":"Bajo: C+R visibles, T no visible","value":"bajo"},{"label":"Intermedio: C+R+T visibles, T≈R","value":"intermedio"},{"label":"Alto: C+T visibles, T>R","value":"alto"}]}],"phrase_template":"Control positivo bajo: {0} / Control positivo alto: {1}","success_message":"Control positivo: Positivo bajo=Intermedio y Positivo alto=Alto — CUMPLE","error_prefix":"Control positivo NO CUMPLE:"}',
    verdict = NULL,
    verdict_message = NULL,
    multi_check_results_json = NULL,
    result_text_pattern = NULL,
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

-- PASO 5: Verificar resultado final — debe mostrar solo los detalles correctos
-- sin VAMAs y con Control negativo/positivo en vama_multi_check
SELECT d.id, d.name, d.evaluation_type, d.verdict
FROM amunet_quality_test_line_detail d
WHERE d.check_id = (SELECT id FROM amunet_quality_check WHERE name = 'QC/2026/00146')
ORDER BY d.sequence;
