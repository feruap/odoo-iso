-- ============================================================
-- CORRECCIÓN COMPLETA: MAVI-07 para todos los PT (cualitativos + competitivos)
--
-- Cambios:
--   A) CUALITATIVOS (81 productos DM/DL/DIAM/DRAM/DEMAM no competitivos):
--      - Agrega/actualiza text_phrase_mapping con lógica cualitativa
--        + patrones #6 y #7 como RECHAZADOS (prueba inválida)
--      - Muestra negativa: patrón #5 = CUMPLE; #1-4, #6, #7 = NO CUMPLE
--      - Muestra positiva: patrón #1-4 = CUMPLE; #5, #6, #7 = NO CUMPLE
--
--   B) COMPETITIVOS (11 productos antidoping/drogas):
--      - Corrige acceptance_criteria (estaba al revés)
--      - Agrega text_phrase_mapping donde faltaba, con lógica invertida
--        + patrones #6 y #7 como RECHAZADOS
--      - Muestra negativa: patrón #1-4 = CUMPLE; #5, #6, #7 = NO CUMPLE
--      - Muestra positiva: patrón #5 = CUMPLE; #1-4, #6, #7 = NO CUMPLE
--
--   C) Análisis abierto QC/2026/00481 (id=910, DMADB01):
--      - Corrige acceptance_criteria en los detalles
--
-- Base de datos: amunet_prod
-- Solicitado por: Diana Flores — Control de Calidad, 2026-09-22
-- ============================================================

BEGIN;

-- ================================================================
-- BLOQUE A: CUALITATIVOS
-- ================================================================

-- A1. Muestra NEGATIVA cualitativa: #5 = CUMPLE, #1-4 = NO CUMPLE, #6/#7 = RECHAZADO
UPDATE amunet_quality_parameter_specification_config c
SET
    acceptance_criteria  = 'Visualización solo de línea control, patrón #5',
    text_phrase_mapping  = '{"positions":[{"type":"select","index":0,"label":"Patrón Observado","options":[{"label":"#1 (Línea T muy intensa)","value":"result_1"},{"label":"#2 (Línea T intensa)","value":"result_2"},{"label":"#3 (Línea T moderada)","value":"result_3"},{"label":"#4 (Línea T tenue)","value":"result_4"},{"label":"#5 (Sin línea T, solo línea C)","value":"result_5"},{"label":"#6 (Sin línea C, con línea T visible)","value":"result_6"},{"label":"#7 (Sin línea C ni línea T)","value":"result_7"},{"label":"N/A (control no disponible)","value":"na"}],"instruction":"Seleccione el patrón visualizado."}],"evaluation":{"rules":[{"result":"result_5","message":"Muestra Negativa: Patrón #5 (sin línea T, solo C) - CUMPLE","verdict":"pass","sample_type":"negative"},{"result":"result_1","message":"Muestra Negativa: Patrón #1 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"negative"},{"result":"result_2","message":"Muestra Negativa: Patrón #2 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"negative"},{"result":"result_3","message":"Muestra Negativa: Patrón #3 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"negative"},{"result":"result_4","message":"Muestra Negativa: Patrón #4 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"negative"},{"result":"result_6","message":"Muestra Negativa: Patrón #6 (sin línea C) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"negative"},{"result":"result_7","message":"Muestra Negativa: Patrón #7 (sin línea C ni T) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"negative"},{"result":"na","message":"Muestra Negativa: Control no disponible - N/A","verdict":"not_applicable","sample_type":"negative"}]},"phrase_template":"Muestra negativa: Patrón {0}","fixed_sample_type":"negative"}',
    write_date           = NOW()
FROM amunet_quality_check_parameter p,
     product_template pt,
     amunet_quality_check_parameter_specification s
WHERE c.parameter_id    = p.id
  AND c.product_tmpl_id = pt.id
  AND c.specification_id = s.id
  AND p.code    = 'MAVI-07'
  AND c.active  = true
  AND s.name    = 'Muestra negativa'
  AND pt.default_code NOT IN (
      'DMADB01','DMADO02','DMDRO01','DMFEN01','DRAM-002',
      'DMACT02','DMADS01','DMAMP02','DMMET02','DMOPI02','DMTHC02'
  )
  AND (pt.default_code ILIKE 'DM%' OR pt.default_code ILIKE 'DL%'
    OR pt.default_code ILIKE 'DIAM%' OR pt.default_code ILIKE 'DRAM%'
    OR pt.default_code ILIKE 'DEMAM%');

-- A2. Muestra POSITIVA cualitativa: #1-4 = CUMPLE, #5 = NO CUMPLE, #6/#7 = RECHAZADO
UPDATE amunet_quality_parameter_specification_config c
SET
    acceptance_criteria  = 'Visualización línea control y línea de prueba, patrón #1, #2, #3 y #4',
    text_phrase_mapping  = '{"positions":[{"type":"select","index":0,"label":"Patrón Observado","options":[{"label":"#1 (Línea T muy intensa)","value":"result_1"},{"label":"#2 (Línea T intensa)","value":"result_2"},{"label":"#3 (Línea T moderada)","value":"result_3"},{"label":"#4 (Línea T tenue)","value":"result_4"},{"label":"#5 (Sin línea T, solo línea C)","value":"result_5"},{"label":"#6 (Sin línea C, con línea T visible)","value":"result_6"},{"label":"#7 (Sin línea C ni línea T)","value":"result_7"},{"label":"N/A (control no disponible)","value":"na"}],"instruction":"Seleccione el patrón visualizado."}],"evaluation":{"rules":[{"result":"result_1","message":"Muestra Positiva: Patrón #1 (líneas C+T) - CUMPLE","verdict":"pass","sample_type":"positive"},{"result":"result_2","message":"Muestra Positiva: Patrón #2 (líneas C+T) - CUMPLE","verdict":"pass","sample_type":"positive"},{"result":"result_3","message":"Muestra Positiva: Patrón #3 (líneas C+T) - CUMPLE","verdict":"pass","sample_type":"positive"},{"result":"result_4","message":"Muestra Positiva: Patrón #4 (líneas C+T) - CUMPLE","verdict":"pass","sample_type":"positive"},{"result":"result_5","message":"Muestra Positiva: Patrón #5 (sin línea T) - NO CUMPLE","verdict":"fail","sample_type":"positive"},{"result":"result_6","message":"Muestra Positiva: Patrón #6 (sin línea C) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"positive"},{"result":"result_7","message":"Muestra Positiva: Patrón #7 (sin línea C ni T) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"positive"},{"result":"na","message":"Muestra Positiva: Control no disponible - N/A","verdict":"not_applicable","sample_type":"positive"}]},"phrase_template":"Muestra positiva: Patrón {0}","fixed_sample_type":"positive"}',
    write_date           = NOW()
FROM amunet_quality_check_parameter p,
     product_template pt,
     amunet_quality_check_parameter_specification s
WHERE c.parameter_id    = p.id
  AND c.product_tmpl_id = pt.id
  AND c.specification_id = s.id
  AND p.code    = 'MAVI-07'
  AND c.active  = true
  AND s.name    = 'Muestra positiva'
  AND pt.default_code NOT IN (
      'DMADB01','DMADO02','DMDRO01','DMFEN01','DRAM-002',
      'DMACT02','DMADS01','DMAMP02','DMMET02','DMOPI02','DMTHC02'
  )
  AND (pt.default_code ILIKE 'DM%' OR pt.default_code ILIKE 'DL%'
    OR pt.default_code ILIKE 'DIAM%' OR pt.default_code ILIKE 'DRAM%'
    OR pt.default_code ILIKE 'DEMAM%');


-- ================================================================
-- BLOQUE B: COMPETITIVOS (lógica invertida)
-- ================================================================

-- B1. Muestra NEGATIVA competitiva: #1-4 = CUMPLE, #5 = NO CUMPLE, #6/#7 = RECHAZADO
UPDATE amunet_quality_parameter_specification_config c
SET
    acceptance_criteria  = 'Visualización línea control y línea de prueba, patrón #1, #2, #3 y #4',
    text_phrase_mapping  = '{"positions":[{"type":"select","index":0,"label":"Patrón Observado","options":[{"label":"#1 (Línea T muy intensa)","value":"result_1"},{"label":"#2 (Línea T intensa)","value":"result_2"},{"label":"#3 (Línea T moderada)","value":"result_3"},{"label":"#4 (Línea T tenue)","value":"result_4"},{"label":"#5 (Sin línea T, solo línea C)","value":"result_5"},{"label":"#6 (Sin línea C, con línea T visible)","value":"result_6"},{"label":"#7 (Sin línea C ni línea T)","value":"result_7"},{"label":"N/A (control no disponible)","value":"na"}],"instruction":"Seleccione el patrón visualizado."}],"evaluation":{"rules":[{"result":"result_1","message":"Muestra Negativa: Patrón #1 (C+T, sin analito) - CUMPLE","verdict":"pass","sample_type":"negative"},{"result":"result_2","message":"Muestra Negativa: Patrón #2 (C+T, sin analito) - CUMPLE","verdict":"pass","sample_type":"negative"},{"result":"result_3","message":"Muestra Negativa: Patrón #3 (C+T, sin analito) - CUMPLE","verdict":"pass","sample_type":"negative"},{"result":"result_4","message":"Muestra Negativa: Patrón #4 (C+T, sin analito) - CUMPLE","verdict":"pass","sample_type":"negative"},{"result":"result_5","message":"Muestra Negativa: Patrón #5 (solo C, analito detectado) - NO CUMPLE","verdict":"fail","sample_type":"negative"},{"result":"result_6","message":"Muestra Negativa: Patrón #6 (sin línea C) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"negative"},{"result":"result_7","message":"Muestra Negativa: Patrón #7 (sin línea C ni T) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"negative"},{"result":"na","message":"Muestra Negativa: Control no disponible - N/A","verdict":"not_applicable","sample_type":"negative"}]},"phrase_template":"Muestra negativa: Patrón {0}","fixed_sample_type":"negative"}',
    write_date           = NOW()
FROM amunet_quality_check_parameter p,
     product_template pt,
     amunet_quality_check_parameter_specification s
WHERE c.parameter_id    = p.id
  AND c.product_tmpl_id = pt.id
  AND c.specification_id = s.id
  AND p.code    = 'MAVI-07'
  AND c.active  = true
  AND s.name    = 'Muestra negativa'
  AND pt.default_code IN (
      'DMADB01','DMADO02','DMDRO01','DMFEN01','DRAM-002',
      'DMACT02','DMADS01','DMAMP02','DMMET02','DMOPI02','DMTHC02'
  );

-- B2. Muestra POSITIVA competitiva: #5 = CUMPLE, #1-4 = NO CUMPLE, #6/#7 = RECHAZADO
UPDATE amunet_quality_parameter_specification_config c
SET
    acceptance_criteria  = 'Visualización solo de línea control, patrón #5',
    text_phrase_mapping  = '{"positions":[{"type":"select","index":0,"label":"Patrón Observado","options":[{"label":"#1 (Línea T muy intensa)","value":"result_1"},{"label":"#2 (Línea T intensa)","value":"result_2"},{"label":"#3 (Línea T moderada)","value":"result_3"},{"label":"#4 (Línea T tenue)","value":"result_4"},{"label":"#5 (Sin línea T, solo línea C)","value":"result_5"},{"label":"#6 (Sin línea C, con línea T visible)","value":"result_6"},{"label":"#7 (Sin línea C ni línea T)","value":"result_7"},{"label":"N/A (control no disponible)","value":"na"}],"instruction":"Seleccione el patrón visualizado."}],"evaluation":{"rules":[{"result":"result_1","message":"Muestra Positiva: Patrón #1 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"positive"},{"result":"result_2","message":"Muestra Positiva: Patrón #2 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"positive"},{"result":"result_3","message":"Muestra Positiva: Patrón #3 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"positive"},{"result":"result_4","message":"Muestra Positiva: Patrón #4 (línea T visible) - NO CUMPLE","verdict":"fail","sample_type":"positive"},{"result":"result_5","message":"Muestra Positiva: Patrón #5 (sin línea T, solo C) - CUMPLE","verdict":"pass","sample_type":"positive"},{"result":"result_6","message":"Muestra Positiva: Patrón #6 (sin línea C) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"positive"},{"result":"result_7","message":"Muestra Positiva: Patrón #7 (sin línea C ni T) - Prueba Inválida - RECHAZADO","verdict":"fail","sample_type":"positive"},{"result":"na","message":"Muestra Positiva: Control no disponible - N/A","verdict":"not_applicable","sample_type":"positive"}]},"phrase_template":"Muestra positiva: Patrón {0}","fixed_sample_type":"positive"}',
    write_date           = NOW()
FROM amunet_quality_check_parameter p,
     product_template pt,
     amunet_quality_check_parameter_specification s
WHERE c.parameter_id    = p.id
  AND c.product_tmpl_id = pt.id
  AND c.specification_id = s.id
  AND p.code    = 'MAVI-07'
  AND c.active  = true
  AND s.name    = 'Muestra positiva'
  AND pt.default_code IN (
      'DMADB01','DMADO02','DMDRO01','DMFEN01','DRAM-002',
      'DMACT02','DMADS01','DMAMP02','DMMET02','DMOPI02','DMTHC02'
  );


-- ================================================================
-- BLOQUE C: Análisis abierto QC/2026/00481 (id=910, DMADB01)
--   El text_phrase_mapping del detail ya tiene lógica competitiva correcta.
--   Solo falta corregir el texto acceptance_criteria que ve el analista.
-- ================================================================

UPDATE amunet_quality_test_line_detail d
SET acceptance_criteria = 'Visualización línea control y línea de prueba, patrón #1, #2, #3 y #4',
    write_date = NOW()
FROM amunet_quality_test_line tl
WHERE d.test_line_id = tl.id
  AND tl.check_id = 910
  AND d.evaluation_type = 'vama_multi_check'
  AND d.acceptance_criteria NOT LIKE '%patrón #1%';

UPDATE amunet_quality_test_line_detail d
SET acceptance_criteria = 'Visualización solo de línea control, patrón #5',
    write_date = NOW()
FROM amunet_quality_test_line tl
WHERE d.test_line_id = tl.id
  AND tl.check_id = 910
  AND d.evaluation_type = 'vama_multi_check'
  AND d.acceptance_criteria LIKE '%patrón #1%';

-- ================================================================
-- Verificación (descomentar para revisar antes del COMMIT)
-- ================================================================
-- SELECT pt.default_code, s.name as spec,
--        c.acceptance_criteria,
--        CASE WHEN c.text_phrase_mapping LIKE '%result_6%' THEN 'OK (#6 presente)'
--             ELSE 'FALTA #6' END as invalidos
-- FROM amunet_quality_parameter_specification_config c
-- JOIN amunet_quality_check_parameter p ON p.id = c.parameter_id
-- JOIN product_template pt ON pt.id = c.product_tmpl_id
-- JOIN amunet_quality_check_parameter_specification s ON s.id = c.specification_id
-- WHERE p.code = 'MAVI-07' AND c.active = true
--   AND s.name = 'Muestra negativa'
--   AND (pt.default_code ILIKE 'DM%' OR pt.default_code ILIKE 'DL%')
-- ORDER BY pt.default_code
-- LIMIT 20;

COMMIT;
