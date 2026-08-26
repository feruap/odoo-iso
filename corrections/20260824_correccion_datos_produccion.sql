-- ============================================================
-- CORRECCIÓN DE DATOS EN PRODUCCIÓN (amunet_prod)
-- Solicitado por: Diana Flores (s.controldecalidad@amunet.com.mx)
-- Fecha: 2026-08-24
-- Motivo: Resultados MAVI-11 no capturados en análisis cerrados;
--         descripciones de producto incorrectas.
-- Autorizado para aplicar por: Mery (desarrollo)
-- ============================================================

BEGIN;

-- ============================================================
-- 1. MAVI-11 — Cartucho Tuberculosis
--    Análisis: QC/2026/00007 | Lote: CAR28072601
-- ============================================================
UPDATE amunet_quality_test_line_detail SET
    result_numeric = 0.1, result_numeric_filled = true
WHERE id = 4611; -- Cierre completo (máx 0.50)

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 3.7, result_numeric_filled = true
WHERE id = 4613; -- Interna (Ventana) Ancho (máx 4.50)

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 15.2, result_numeric_filled = true
WHERE id = 4612; -- Interna (Ventana) Largo (máx 18.00)

-- ============================================================
-- 2. MAVI-11 — Cartucho Calprotectina
--    Análisis: QC/2026/00032 | Lote: CAR55072601
-- ============================================================
UPDATE amunet_quality_test_line_detail SET
    result_numeric = 0.1, result_numeric_filled = true
WHERE id = 4820; -- Cierre completo

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 3.2, result_numeric_filled = true
WHERE id = 4822; -- Interna (Ventana) Ancho

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 14.5, result_numeric_filled = true
WHERE id = 4821; -- Interna (Ventana) Largo

-- ============================================================
-- 3. MAVI-11 — Cartucho Entamoeba
--    Análisis: QC/2026/00033 | Lote: CAR48072601
-- ============================================================
UPDATE amunet_quality_test_line_detail SET
    result_numeric = 0.1, result_numeric_filled = true
WHERE id = 4831; -- Cierre completo

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 2.8, result_numeric_filled = true
WHERE id = 4833; -- Interna (Ventana) Ancho

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 14.5, result_numeric_filled = true
WHERE id = 4832; -- Interna (Ventana) Largo

-- ============================================================
-- 4. MAVI-11 — Cartucho Factor Reumatoide
--    Análisis: QC/2026/00035 | Lote: CAR42072601
-- ============================================================
UPDATE amunet_quality_test_line_detail SET
    result_numeric = 0.1, result_numeric_filled = true
WHERE id = 4853; -- Cierre completo

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 2.3, result_numeric_filled = true
WHERE id = 4855; -- Interna (Ventana) Ancho

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 14.0, result_numeric_filled = true
WHERE id = 4854; -- Interna (Ventana) Largo

-- ============================================================
-- 5. MAVI-11 — Cartucho Chagas
--    Análisis: QC/2026/00034 | Lote: CAR05072601
-- ============================================================
UPDATE amunet_quality_test_line_detail SET
    result_numeric = 0.1, result_numeric_filled = true
WHERE id = 4842; -- Cierre completo

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 2.5, result_numeric_filled = true
WHERE id = 4844; -- Interna (Ventana) Ancho

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 14.0, result_numeric_filled = true
WHERE id = 4843; -- Interna (Ventana) Largo

-- ============================================================
-- 6. Agentes biológicos — Agua Bidestilada
--    Análisis: QC/2026/00017 | Lote: ABI01082601
--    Valor: < 1 UFC (se registra como 0 en campo numérico)
-- ============================================================
UPDATE amunet_quality_test_line_detail SET
    result_numeric = 0, result_numeric_filled = true
WHERE id = 5933; -- Agentes biológicos (criterio: ≤100 UFC/10 mL)

-- ============================================================
-- 7. Descripción — MPCAR53 Cartucho Antidoping 5P saliva
--    Cambio permanente a nivel producto
-- ============================================================
UPDATE product_template SET
    description = '{"en_US": "<p>Cartucho para prueba rápida de antidoping 5 parámetros en muestras de saliva</p>", "es_MX": "<p>Cartucho para prueba rápida de antidoping 5 parámetros en muestras de saliva</p>"}'::jsonb
WHERE default_code = 'MPCAR53';

-- ============================================================
-- 8. Descripción — SPHMC53 Hoja Maestra Antidoping 2P saliva
-- ============================================================
UPDATE product_template SET
    description = '{"en_US": "<p>Hoja maestra para la detección de Antidoping 2 parámetros (MET y THC) en muestras de saliva</p>", "es_MX": "<p>Hoja maestra para la detección de Antidoping 2 parámetros (MET y THC) en muestras de saliva</p>"}'::jsonb
WHERE default_code = 'SPHMC53';

-- ============================================================
-- 9. Descripción — SPHMC54 Hoja Maestra Antidoping 3P saliva
-- ============================================================
UPDATE product_template SET
    description = '{"en_US": "<p>Hoja maestra para la detección de Antidoping 3 parámetros (OPI, COC y AMP) en muestras de saliva</p>", "es_MX": "<p>Hoja maestra para la detección de Antidoping 3 parámetros (OPI, COC y AMP) en muestras de saliva</p>"}'::jsonb
WHERE default_code = 'SPHMC54';

-- ============================================================
-- 10. Descripciones — Buffers de proveedor STBPR01-04 + STREX01-02
-- ============================================================
UPDATE product_template SET description='{"es_MX": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras de sangre, suero o plasma</p>", "en_US": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras de sangre, suero o plasma</p>"}'::jsonb WHERE default_code='STBPR01';
UPDATE product_template SET description='{"es_MX": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras orofaríngeas, nasofaríngeas o salivales</p>", "en_US": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras orofaríngeas, nasofaríngeas o salivales</p>"}'::jsonb WHERE default_code='STBPR02';
UPDATE product_template SET description='{"es_MX": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras de heces</p>", "en_US": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras de heces</p>"}'::jsonb WHERE default_code='STBPR03';
UPDATE product_template SET description='{"es_MX": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras HV</p>", "en_US": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras HV</p>"}'::jsonb WHERE default_code='STBPR04';
UPDATE product_template SET description='{"es_MX": "<p>Vial con reactivo de extracción 1 para pruebas rápidas</p>", "en_US": "<p>Vial con reactivo de extracción 1 para pruebas rápidas</p>"}'::jsonb WHERE default_code='STREX01';
UPDATE product_template SET description='{"es_MX": "<p>Vial con reactivo de extracción 2 para pruebas rápidas</p>", "en_US": "<p>Vial con reactivo de extracción 2 para pruebas rápidas</p>"}'::jsonb WHERE default_code='STREX02';

-- ============================================================
-- 11. Descripción — STBPC01 (clave conjunta buffers de proveedor)
--     NOTA: STBPC01 solo existe en producción, no en staging.
-- ============================================================
UPDATE product_template SET description='{"es_MX": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas</p>", "en_US": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas</p>"}'::jsonb WHERE default_code='STBPC01';

-- ============================================================
-- 12. MAVI-11 Goteros (STGOT01-07): limpiar specs extra y aplicar ±5mm
--     Solo quedan activas Punta del gotero y Largo del gotero
-- ============================================================
UPDATE amunet_quality_parameter_specification_config cfg SET active=false
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON pt.id=rel.product_tmpl_id
WHERE cfg.product_parameter_rel_id=rel.id
  AND rel.parameter_code='MAVI-11'
  AND pt.default_code IN ('STGOT01','STGOT02','STGOT03','STGOT04','STGOT05','STGOT06','STGOT07')
  AND cfg.specification_name NOT IN ('Punta del gotero','Largo del gotero');

UPDATE amunet_quality_parameter_specification_config cfg SET
    tolerance=5, sequence=10,
    min_value=CASE WHEN nominal_value>0 THEN nominal_value-5 ELSE min_value END,
    max_value=CASE WHEN nominal_value>0 THEN nominal_value+5 ELSE max_value END
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON pt.id=rel.product_tmpl_id
WHERE cfg.product_parameter_rel_id=rel.id AND rel.parameter_code='MAVI-11'
  AND pt.default_code LIKE 'STGOT%' AND cfg.specification_name='Punta del gotero';

UPDATE amunet_quality_parameter_specification_config cfg SET
    tolerance=5, sequence=20,
    min_value=CASE WHEN nominal_value>0 THEN nominal_value-5 ELSE min_value END,
    max_value=CASE WHEN nominal_value>0 THEN nominal_value+5 ELSE max_value END
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON pt.id=rel.product_tmpl_id
WHERE cfg.product_parameter_rel_id=rel.id AND rel.parameter_code='MAVI-11'
  AND pt.default_code LIKE 'STGOT%' AND cfg.specification_name='Largo del gotero';

-- ============================================================
-- 13. MAVI-17 Goteros: rango volumen 4-11 µl (mínimo real evita 0 gotas)
-- ============================================================
UPDATE amunet_quality_parameter_specification_config cfg SET
    min_value=4, max_value=11
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON pt.id=rel.product_tmpl_id
WHERE cfg.product_parameter_rel_id=rel.id AND rel.parameter_code='MAVI-17'
  AND pt.default_code LIKE 'STGOT%';

-- ============================================================
-- 14. Buffers (STBPR01-04, STREX01-02, STHEB01): MAVI-07 vama_multi_check
--     Muestra positiva: seq=10, criterio correcto
--     Muestra negativa: seq=20, criterio correcto
-- ============================================================
UPDATE amunet_quality_parameter_specification_config cfg SET
    evaluation_type='vama_multi_check', sequence=10,
    acceptance_criteria='Patrones #1-#4 (Línea T visible)'
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON pt.id=rel.product_tmpl_id
WHERE cfg.product_parameter_rel_id=rel.id AND rel.parameter_code='MAVI-07'
  AND cfg.specification_id=629
  AND pt.default_code IN ('STBPR01','STBPR02','STBPR03','STBPR04','STREX01','STREX02','STHEB01');

UPDATE amunet_quality_parameter_specification_config cfg SET
    evaluation_type='vama_multi_check', sequence=20,
    acceptance_criteria='Patrón #5 (Solo línea control, sin línea T)'
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON pt.id=rel.product_tmpl_id
WHERE cfg.product_parameter_rel_id=rel.id AND rel.parameter_code='MAVI-07'
  AND cfg.specification_id=628
  AND pt.default_code IN ('STBPR01','STBPR02','STBPR03','STBPR04','STREX01','STREX02','STHEB01');

-- Limpiar binary_option_pass/fail para vama_multi_check en buffers
UPDATE amunet_quality_parameter_specification_config cfg SET
    binary_option_pass=NULL, binary_option_fail=NULL
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON pt.id=rel.product_tmpl_id
WHERE cfg.product_parameter_rel_id=rel.id AND rel.parameter_code='MAVI-07'
  AND cfg.evaluation_type='vama_multi_check'
  AND pt.default_code IN ('STBPR01','STBPR02','STBPR03','STBPR04','STREX01','STREX02','STHEB01');

-- ============================================================
-- 15. PT cualitativos (Pruebas rápidas): MAVI-07 mavi_07_ternary → vama_multi_check
-- ============================================================
UPDATE amunet_quality_parameter_specification_config cfg SET
    evaluation_type='vama_multi_check', sequence=10,
    acceptance_criteria='Patrones #1-#4 (Línea T visible)'
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON pt.id=rel.product_tmpl_id
JOIN product_category cat ON cat.id=pt.categ_id
WHERE cfg.product_parameter_rel_id=rel.id AND rel.parameter_code='MAVI-07'
  AND cfg.specification_id=629 AND cfg.evaluation_type='mavi_07_ternary'
  AND cat.complete_name LIKE '%Pruebas rápidas%';

UPDATE amunet_quality_parameter_specification_config cfg SET
    evaluation_type='vama_multi_check', sequence=20,
    acceptance_criteria='Patrón #5 (Solo línea control, sin línea T)'
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON pt.id=rel.product_tmpl_id
JOIN product_category cat ON cat.id=pt.categ_id
WHERE cfg.product_parameter_rel_id=rel.id AND rel.parameter_code='MAVI-07'
  AND cfg.specification_id=628 AND cfg.evaluation_type='mavi_07_ternary'
  AND cat.complete_name LIKE '%Pruebas rápidas%';

-- ============================================================
-- 16. PT cualitativos: MAVI-09 rangos — Liberación 0-30s, Migración 30-180s
--     Excepción Dengue (DMDEN01, DMDEN02): Migración 30-240s
-- ============================================================
UPDATE amunet_quality_parameter_specification_config cfg SET
    min_value=0, max_value=30, specification_name='Tiempo de liberación'
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON pt.id=rel.product_tmpl_id
JOIN product_category cat ON cat.id=pt.categ_id
WHERE cfg.product_parameter_rel_id=rel.id AND rel.parameter_code='MAVI-09'
  AND cfg.specification_name ILIKE '%liberaci%'
  AND cfg.min_value=0 AND cfg.max_value=0
  AND cat.complete_name LIKE '%Pruebas rápidas%';

UPDATE amunet_quality_parameter_specification_config cfg SET
    min_value=30, max_value=180, specification_name='Tiempo de migración'
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON pt.id=rel.product_tmpl_id
JOIN product_category cat ON cat.id=pt.categ_id
WHERE cfg.product_parameter_rel_id=rel.id AND rel.parameter_code='MAVI-09'
  AND cfg.specification_name ILIKE '%migraci%'
  AND cfg.min_value=0 AND cfg.max_value=0
  AND cat.complete_name LIKE '%Pruebas rápidas%'
  AND pt.default_code NOT IN ('DMDEN01','DMDEN02');

UPDATE amunet_quality_parameter_specification_config cfg SET
    min_value=30, max_value=240, specification_name='Tiempo de migración'
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON pt.id=rel.product_tmpl_id
WHERE cfg.product_parameter_rel_id=rel.id AND rel.parameter_code='MAVI-09'
  AND cfg.specification_name ILIKE '%migraci%'
  AND cfg.min_value=0 AND cfg.max_value=0
  AND pt.default_code IN ('DMDEN01','DMDEN02');

-- ============================================================
-- 17. PT cualitativos: INC-002 opciones de selección binaria
-- ============================================================
UPDATE amunet_quality_parameter_specification_config cfg SET
    binary_option_pass='Cumple', binary_option_fail='No cumple'
FROM amunet_quality_parameter_product_rel rel
JOIN product_template pt ON pt.id=rel.product_tmpl_id
JOIN product_category cat ON cat.id=pt.categ_id
WHERE cfg.product_parameter_rel_id=rel.id AND rel.parameter_code='INC-002'
  AND (cfg.binary_option_pass IS NULL OR cfg.binary_option_pass='')
  AND cat.complete_name LIKE '%Pruebas rápidas%';

-- ============================================================
-- 18. Nuevos productos con puntos de control copiados desde DMHBC01:
--     DMPSA02 (Prostatinet) y DMHPY01 (H. pylori)
--     (5 parámetros: INC-002, MAVI-04, MAVI-07, MAVI-09, MGA-0486)
-- ============================================================
DO $$
DECLARE
    src_tmpl_id INTEGER;
    tgt_tmpl_id INTEGER;
    src_rel RECORD;
    tgt_rel_id INTEGER;
    tgt_code TEXT;
BEGIN
    SELECT id INTO src_tmpl_id FROM product_template WHERE default_code='DMHBC01';
    FOREACH tgt_code IN ARRAY ARRAY['DMPSA02','DMHPY01'] LOOP
        SELECT id INTO tgt_tmpl_id FROM product_template WHERE default_code=tgt_code;
        IF tgt_tmpl_id IS NULL THEN CONTINUE; END IF;
        -- Evitar duplicados
        IF EXISTS (SELECT 1 FROM amunet_quality_parameter_product_rel WHERE product_tmpl_id=tgt_tmpl_id) THEN
            RAISE NOTICE '% ya tiene parámetros, omitiendo', tgt_code; CONTINUE;
        END IF;
        FOR src_rel IN SELECT * FROM amunet_quality_parameter_product_rel WHERE product_tmpl_id=src_tmpl_id LOOP
            INSERT INTO amunet_quality_parameter_product_rel
                (product_tmpl_id,parameter_id,sequence,company_id,parameter_code,parameter_name,active,create_uid,write_uid,create_date,write_date)
            VALUES(tgt_tmpl_id,src_rel.parameter_id,src_rel.sequence,src_rel.company_id,src_rel.parameter_code,src_rel.parameter_name,src_rel.active,2,2,NOW(),NOW())
            RETURNING id INTO tgt_rel_id;
            INSERT INTO amunet_quality_parameter_specification_config
                (product_parameter_rel_id,specification_id,sequence,uom_id,product_tmpl_id,parameter_id,company_id,specification_name,evaluation_type,acceptance_criteria,binary_prefix,binary_suffix,binary_expected_option,binary_option_pass,binary_option_fail,checkbox_label_1,checkbox_label_2,text_pattern_expected,text_pattern_regex,text_phrase_mapping,nominal_value,tolerance,min_value,max_value,min_value_manual,max_value_manual,active,use_manual_range,checkbox_require_both,binary_notes_required,binary_notes_option_pass,binary_notes_option_fail,ternary_option_yes,ternary_option_no,ternary_option_na,range_display,text_pattern_length,create_uid,write_uid,create_date,write_date)
            SELECT tgt_rel_id,specification_id,sequence,uom_id,tgt_tmpl_id,parameter_id,company_id,specification_name,evaluation_type,acceptance_criteria,binary_prefix,binary_suffix,binary_expected_option,binary_option_pass,binary_option_fail,checkbox_label_1,checkbox_label_2,text_pattern_expected,text_pattern_regex,text_phrase_mapping,nominal_value,tolerance,min_value,max_value,min_value_manual,max_value_manual,active,use_manual_range,checkbox_require_both,binary_notes_required,binary_notes_option_pass,binary_notes_option_fail,ternary_option_yes,ternary_option_no,ternary_option_na,range_display,text_pattern_length,2,2,NOW(),NOW()
            FROM amunet_quality_parameter_specification_config WHERE product_parameter_rel_id=src_rel.id;
        END LOOP;
    END LOOP;
END $$;

COMMIT;

-- Verificación rápida post-aplicación:
SELECT 'TB Cierre' as campo, result_numeric FROM amunet_quality_test_line_detail WHERE id=4611
UNION ALL SELECT 'TB Ancho', result_numeric FROM amunet_quality_test_line_detail WHERE id=4613
UNION ALL SELECT 'TB Largo', result_numeric FROM amunet_quality_test_line_detail WHERE id=4612
UNION ALL SELECT 'Calp Cierre', result_numeric FROM amunet_quality_test_line_detail WHERE id=4820
UNION ALL SELECT 'Calp Ancho', result_numeric FROM amunet_quality_test_line_detail WHERE id=4822
UNION ALL SELECT 'Calp Largo', result_numeric FROM amunet_quality_test_line_detail WHERE id=4821
UNION ALL SELECT 'Enta Cierre', result_numeric FROM amunet_quality_test_line_detail WHERE id=4831
UNION ALL SELECT 'Enta Ancho', result_numeric FROM amunet_quality_test_line_detail WHERE id=4833
UNION ALL SELECT 'Enta Largo', result_numeric FROM amunet_quality_test_line_detail WHERE id=4832
UNION ALL SELECT 'FR Cierre', result_numeric FROM amunet_quality_test_line_detail WHERE id=4853
UNION ALL SELECT 'FR Ancho', result_numeric FROM amunet_quality_test_line_detail WHERE id=4855
UNION ALL SELECT 'FR Largo', result_numeric FROM amunet_quality_test_line_detail WHERE id=4854
UNION ALL SELECT 'Chagas Cierre', result_numeric FROM amunet_quality_test_line_detail WHERE id=4842
UNION ALL SELECT 'Chagas Ancho', result_numeric FROM amunet_quality_test_line_detail WHERE id=4844
UNION ALL SELECT 'Chagas Largo', result_numeric FROM amunet_quality_test_line_detail WHERE id=4843
UNION ALL SELECT 'ABI Agentes bio', result_numeric FROM amunet_quality_test_line_detail WHERE id=5933;
