-- ============================================================
-- FIX ANÁLISIS 888 (QC/2026/00146 — DMPSA01 PSA semicuantitativa)
-- v3 — 2026-09-08
-- Corrige: test_line_id obligatorio; crea líneas de prueba
--          para MGA-0486 e INC-002 antes de insertar detalles.
-- ============================================================

DO $$
DECLARE
    v_check_id        INTEGER;
    v_param_mga       INTEGER;
    v_param_inc       INTEGER;
    v_param_mavi15    INTEGER;
    v_line_mavi07     INTEGER;
    v_line_mga        INTEGER;
    v_line_inc        INTEGER;
BEGIN

    -- 1. ID del análisis en esta base
    SELECT id INTO v_check_id
    FROM amunet_quality_check WHERE name = 'QC/2026/00146';

    IF v_check_id IS NULL THEN
        RAISE EXCEPTION 'No se encontró el análisis QC/2026/00146 en esta base';
    END IF;
    RAISE NOTICE 'check_id = %', v_check_id;

    -- 2. IDs de parámetros (resueltos por código, no hardcodeados)
    SELECT id INTO v_param_mga   FROM amunet_quality_check_parameter WHERE code = 'MGA-0486' LIMIT 1;
    SELECT id INTO v_param_inc   FROM amunet_quality_check_parameter WHERE code = 'INC-002'  LIMIT 1;
    SELECT id INTO v_param_mavi15 FROM amunet_quality_check_parameter WHERE code = 'MAVI-15' LIMIT 1;

    RAISE NOTICE 'MGA-0486 param_id=%, INC-002 param_id=%, MAVI-15 param_id=%',
        v_param_mga, v_param_inc, v_param_mavi15;

    -- ================================================================
    -- BLOQUE A: Reactivar MGA-0486 e INC-002 en la configuración del producto
    -- ================================================================
    UPDATE amunet_quality_parameter_product_rel r
    SET active = true, write_date = NOW()
    FROM amunet_quality_check_parameter p, product_template pt
    WHERE p.id = r.parameter_id
      AND pt.id = r.product_tmpl_id
      AND pt.default_code IN ('DMPSA01','DMTSH02','DMFRT02')
      AND p.code IN ('MGA-0486','INC-002')
      AND r.active = false;

    RAISE NOTICE 'Parámetros reactivados en producto: %', FOUND;

    -- ================================================================
    -- BLOQUE B: Convertir test_line de MAVI-07 → MAVI-15
    -- ================================================================
    SELECT id INTO v_line_mavi07
    FROM amunet_quality_test_line
    WHERE check_id = v_check_id
      AND (name ILIKE '%visualiz%' OR name ILIKE '%lineas%' OR parameter_id = (
            SELECT id FROM amunet_quality_check_parameter WHERE code = 'MAVI-07' LIMIT 1))
    LIMIT 1;

    IF v_line_mavi07 IS NOT NULL THEN
        UPDATE amunet_quality_test_line
        SET parameter_id = v_param_mavi15,
            name = 'Visualizacion de lineas semicuantitativas',
            write_date = NOW()
        WHERE id = v_line_mavi07;
        RAISE NOTICE 'test_line MAVI-07→MAVI-15 actualizada: id=%', v_line_mavi07;
    ELSE
        -- Si no existe, crearla
        INSERT INTO amunet_quality_test_line
            (check_id, parameter_id, name, sequence, detail_count,
             create_date, write_date, create_uid, write_uid)
        VALUES (v_check_id, v_param_mavi15, 'Visualizacion de lineas semicuantitativas',
                40, 0, NOW(), NOW(), 1, 1)
        RETURNING id INTO v_line_mavi07;
        RAISE NOTICE 'test_line MAVI-15 creada: id=%', v_line_mavi07;
    END IF;

    -- Convertir detalles Control negativo
    UPDATE amunet_quality_test_line_detail
    SET name = 'Control negativo',
        evaluation_type = 'vama_multi_check',
        test_line_id = v_line_mavi07,
        text_phrase_mapping = '{"fixed_sample_type":"negative","positions":[{"index":0,"type":"select","label":"Intensidad observada (PRS-01)","instruction":"Seleccione el nivel de la línea T respecto a la línea R.","options":[{"label":"Bajo: C+R visibles, T no visible","value":"bajo"},{"label":"Intermedio: C+R+T visibles, T≈R","value":"intermedio"},{"label":"Alto: C+T visibles, T>R","value":"alto"}]}],"phrase_template":"Control negativo: {0}","evaluation":{"rules":[{"sample_type":"negative","result":"bajo","verdict":"pass","message":"Control negativo: Bajo (T no visible) — CUMPLE"},{"sample_type":"negative","result":"intermedio","verdict":"fail","message":"Control negativo: Intermedio — NO CUMPLE"},{"sample_type":"negative","result":"alto","verdict":"fail","message":"Control negativo: Alto — NO CUMPLE"}]}}',
        verdict = NULL, verdict_message = NULL,
        multi_check_results_json = NULL, result_text_pattern = NULL,
        write_date = NOW()
    WHERE check_id = v_check_id
      AND name ILIKE '%negativ%';

    -- Convertir detalles Control positivo
    UPDATE amunet_quality_test_line_detail
    SET name = 'Control positivo',
        evaluation_type = 'vama_multi_check',
        test_line_id = v_line_mavi07,
        text_phrase_mapping = '{"fixed_sample_type":"positive","positions":[{"index":0,"type":"select","label":"Positivo bajo — intensidad de la línea T","instruction":"Seleccione el nivel de la línea T respecto a la línea R.","pass_value":"intermedio","options":[{"label":"Bajo: C+R visibles, T no visible","value":"bajo"},{"label":"Intermedio: C+R+T visibles, T≈R","value":"intermedio"},{"label":"Alto: C+T visibles, T>R","value":"alto"}]},{"index":1,"type":"select","label":"Positivo alto — intensidad de la línea T","instruction":"Seleccione el nivel de la línea T respecto a la línea R.","pass_value":"alto","options":[{"label":"Bajo: C+R visibles, T no visible","value":"bajo"},{"label":"Intermedio: C+R+T visibles, T≈R","value":"intermedio"},{"label":"Alto: C+T visibles, T>R","value":"alto"}]}],"phrase_template":"Control positivo bajo: {0} / Control positivo alto: {1}","success_message":"Control positivo: Positivo bajo=Intermedio y Positivo alto=Alto — CUMPLE","error_prefix":"Control positivo NO CUMPLE:"}',
        verdict = NULL, verdict_message = NULL,
        multi_check_results_json = NULL, result_text_pattern = NULL,
        write_date = NOW()
    WHERE check_id = v_check_id
      AND name ILIKE '%positiv%';

    -- ================================================================
    -- BLOQUE C: Eliminar líneas VAMA (detalles y líneas de prueba)
    -- ================================================================
    DELETE FROM amunet_quality_test_line_detail
    WHERE check_id = v_check_id
      AND (name ILIKE 'VAMA%'
           OR name ILIKE '%etiqueta%'
           OR name ILIKE '%instructivo%'
           OR name ILIKE '%termosellado%'
           OR name ILIKE '%gotero%'
           OR name ILIKE '%vial%');

    DELETE FROM amunet_quality_test_line
    WHERE check_id = v_check_id
      AND parameter_id IN (
          SELECT id FROM amunet_quality_check_parameter
          WHERE code IN ('VAMA-034','VAMA-036','VAMA-064','VAMA-091','VAMA-038','VAMA-096')
      );

    -- ================================================================
    -- BLOQUE D: Agregar test_line + detalle para MGA-0486 si no existen
    -- ================================================================
    SELECT id INTO v_line_mga
    FROM amunet_quality_test_line
    WHERE check_id = v_check_id AND parameter_id = v_param_mga
    LIMIT 1;

    IF v_line_mga IS NULL THEN
        INSERT INTO amunet_quality_test_line
            (check_id, parameter_id, name, sequence, detail_count,
             create_date, write_date, create_uid, write_uid)
        VALUES (v_check_id, v_param_mga, 'Hermeticidad', 20, 1, NOW(), NOW(), 1, 1)
        RETURNING id INTO v_line_mga;
        RAISE NOTICE 'test_line MGA-0486 creada: id=%', v_line_mga;
    END IF;

    INSERT INTO amunet_quality_test_line_detail
        (check_id, test_line_id, name, evaluation_type, acceptance_criteria,
         binary_option_pass, binary_option_fail, expected_value_binary,
         sequence, verdict, create_date, write_date, create_uid, write_uid)
    SELECT v_check_id, v_line_mga,
           'Prueba de colorante', 'binary_selection', 'Ausencia de colorante',
           'Ausencia de colorante', 'Presencia de colorante', 'pass',
           1, NULL, NOW(), NOW(), 1, 1
    WHERE NOT EXISTS (
        SELECT 1 FROM amunet_quality_test_line_detail
        WHERE check_id = v_check_id AND test_line_id = v_line_mga
    );

    -- ================================================================
    -- BLOQUE E: Agregar test_line + detalle para INC-002 si no existen
    -- ================================================================
    SELECT id INTO v_line_inc
    FROM amunet_quality_test_line
    WHERE check_id = v_check_id AND parameter_id = v_param_inc
    LIMIT 1;

    IF v_line_inc IS NULL THEN
        INSERT INTO amunet_quality_test_line
            (check_id, parameter_id, name, sequence, detail_count,
             create_date, write_date, create_uid, write_uid)
        VALUES (v_check_id, v_param_inc, 'Verificación de contenido de empaque', 90, 1, NOW(), NOW(), 1, 1)
        RETURNING id INTO v_line_inc;
        RAISE NOTICE 'test_line INC-002 creada: id=%', v_line_inc;
    END IF;

    INSERT INTO amunet_quality_test_line_detail
        (check_id, test_line_id, name, evaluation_type, acceptance_criteria,
         binary_option_pass, binary_option_fail, expected_value_binary,
         sequence, verdict, create_date, write_date, create_uid, write_uid)
    SELECT v_check_id, v_line_inc,
           'Verificación de contenido de empaque', 'binary_selection',
           'El contenido coincide con el especificado en el manual.',
           'Contenido coincide', 'Contenido no coincide', 'pass',
           10, NULL, NOW(), NOW(), 1, 1
    WHERE NOT EXISTS (
        SELECT 1 FROM amunet_quality_test_line_detail
        WHERE check_id = v_check_id AND test_line_id = v_line_inc
    );

    RAISE NOTICE 'Fix completado para análisis %', v_check_id;
END;
$$;

-- ================================================================
-- VERIFICACIÓN FINAL — compartir resultado con Diana
-- ================================================================
SELECT tl.name AS linea, d.name AS detalle, d.evaluation_type, d.verdict
FROM amunet_quality_test_line_detail d
JOIN amunet_quality_test_line tl ON tl.id = d.test_line_id
WHERE d.check_id = (SELECT id FROM amunet_quality_check WHERE name = 'QC/2026/00146')
ORDER BY tl.sequence, d.sequence;
