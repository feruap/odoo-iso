-- ============================================================
-- FIX ANÁLISIS 893 (QC/2026/00153 — DMTOR02 ToRCH IgG/IgM PT)
-- Preparado por: Calidad (Diana Flores)
-- Fecha: 2026-09-08
-- Ejecutar en la base de PRODUCCIÓN (amunet_prod)
--
-- Cambios en el análisis 893:
--   1. Eliminar líneas VAMA-034/036/064/091/038/096 y MAVI-13
--   2. Eliminar "Interpretación de Líneas" de MAVI-07
--   3. Renombrar "Sellado" → "Letra adecuada" en MAVI-04
--   4. Corregir rangos MAVI-09: Liberación 1-30s, Migración 30-180s
--   5. Reordenar: MAVI-04=10, MGA-0486=20, MAVI-09=30, MAVI-07=40, INC-002=50
--   6. Agregar test_line + detalle para MGA-0486 (Hermeticidad)
--   7. Agregar test_line + detalle para INC-002 (Verificación de contenido)
--   8. Configurar anexo igual que hemoglobina (análisis QC/2026/00130)
--
-- Cambios en la configuración del producto DMTOR02 (para análisis futuros):
--   9. Desactivar rels VAMA/MAVI-13
--  10. Crear rel + spec_config para MGA-0486 e INC-002
--  11. Limpiar exceso de specs MAVI-09 (dejar solo Liberación y Migración)
-- ============================================================

DO $$
DECLARE
    v_check_id      INTEGER := 893;
    v_tmpl_id       INTEGER := 1336;  -- product_template DMTOR02

    -- Parámetros (resueltos por código)
    v_param_mga     INTEGER;
    v_param_inc     INTEGER;
    v_param_mavi09  INTEGER;
    v_param_mavi07  INTEGER;

    -- Specs base (resueltas por nombre)
    v_spec_colorante    INTEGER;  -- MGA-0486: "Prueba de colorante" (spec_id=100)
    v_spec_inc          INTEGER;  -- INC-002: "Verificación de contenido de empaque" (spec_id=709)

    -- Rels para el producto
    v_rel_mga   INTEGER;
    v_rel_inc   INTEGER;

    -- Spec_configs nuevas
    v_sc_mga    INTEGER;
    v_sc_inc    INTEGER;

    -- Test lines nuevas en el análisis
    v_line_mga  INTEGER;
    v_line_inc  INTEGER;

BEGIN
    -- ========================================================
    -- PARTE 1: Resolver IDs de parámetros
    -- ========================================================
    SELECT id INTO v_param_mga  FROM amunet_quality_check_parameter WHERE code = 'MGA-0486' LIMIT 1;
    SELECT id INTO v_param_inc  FROM amunet_quality_check_parameter WHERE code = 'INC-002'  LIMIT 1;
    SELECT id INTO v_param_mavi09 FROM amunet_quality_check_parameter WHERE code = 'MAVI-09' LIMIT 1;
    SELECT id INTO v_param_mavi07 FROM amunet_quality_check_parameter WHERE code = 'MAVI-07' LIMIT 1;

    -- Specs base
    SELECT id INTO v_spec_colorante
    FROM amunet_quality_check_parameter_specification
    WHERE parameter_id = v_param_mga AND name = 'Prueba de colorante' LIMIT 1;

    SELECT id INTO v_spec_inc
    FROM amunet_quality_check_parameter_specification
    WHERE parameter_id = v_param_inc AND name = 'Verificación de contenido de empaque' LIMIT 1;

    RAISE NOTICE 'Params: MGA=%, INC=%, MAVI09=%, MAVI07=%', v_param_mga, v_param_inc, v_param_mavi09, v_param_mavi07;
    RAISE NOTICE 'Specs: colorante=%, inc=%', v_spec_colorante, v_spec_inc;

    -- ========================================================
    -- PARTE 2: Limpiar el análisis 893
    -- ========================================================

    -- 2a. Eliminar detalles de VAMA/MAVI-13
    DELETE FROM amunet_quality_test_line_detail
    WHERE check_id = v_check_id
      AND test_line_id IN (
          SELECT tl.id FROM amunet_quality_test_line tl
          JOIN amunet_quality_check_parameter p ON p.id = tl.parameter_id
          WHERE tl.check_id = v_check_id
            AND p.code IN ('VAMA-034','VAMA-036','VAMA-064','VAMA-091','VAMA-038','VAMA-096','MAVI-13')
      );

    -- 2b. Eliminar líneas VAMA/MAVI-13
    DELETE FROM amunet_quality_test_line
    WHERE check_id = v_check_id
      AND parameter_id IN (
          SELECT id FROM amunet_quality_check_parameter
          WHERE code IN ('VAMA-034','VAMA-036','VAMA-064','VAMA-091','VAMA-038','VAMA-096','MAVI-13')
      );
    RAISE NOTICE 'VAMA/MAVI-13 eliminados';

    -- 2c. Eliminar "Interpretación de Líneas" de MAVI-07
    DELETE FROM amunet_quality_test_line_detail
    WHERE check_id = v_check_id
      AND name ILIKE '%interpretaci%';
    RAISE NOTICE 'Interpretación de Líneas eliminada de MAVI-07';

    -- 2d. Renombrar "Sellado" → "Letra adecuada" en MAVI-04
    UPDATE amunet_quality_test_line_detail
    SET name = 'Letra adecuada', write_date = NOW()
    WHERE check_id = v_check_id
      AND name = 'Sellado'
      AND binary_option_pass = 'Letra adecuada';
    RAISE NOTICE 'Sellado renombrado a Letra adecuada';

    -- 2e. Corregir rangos MAVI-09
    UPDATE amunet_quality_test_line_detail
    SET min_value = 1, max_value = 30,
        acceptance_criteria = '1-30 segundos',
        write_date = NOW()
    WHERE check_id = v_check_id
      AND name ILIKE '%liberaci%' AND evaluation_type = 'numeric_range';

    UPDATE amunet_quality_test_line_detail
    SET min_value = 30, max_value = 180,
        acceptance_criteria = '30-180 segundos',
        write_date = NOW()
    WHERE check_id = v_check_id
      AND name ILIKE '%migraci%' AND evaluation_type = 'numeric_range';
    RAISE NOTICE 'Rangos MAVI-09 corregidos';

    -- 2f. Reordenar secuencias de líneas de prueba
    UPDATE amunet_quality_test_line SET sequence = 10, write_date = NOW()
    WHERE check_id = v_check_id AND parameter_id = (SELECT id FROM amunet_quality_check_parameter WHERE code='MAVI-04' AND name='Aspectos Visuales' LIMIT 1);

    UPDATE amunet_quality_test_line SET sequence = 30, write_date = NOW()
    WHERE check_id = v_check_id AND parameter_id = v_param_mavi09;

    UPDATE amunet_quality_test_line SET sequence = 40, write_date = NOW()
    WHERE check_id = v_check_id AND parameter_id = v_param_mavi07;
    RAISE NOTICE 'Secuencias reordenadas';

    -- ========================================================
    -- PARTE 3: Crear rel + spec_config para MGA-0486
    -- ========================================================
    SELECT id INTO v_rel_mga
    FROM amunet_quality_parameter_product_rel
    WHERE product_tmpl_id = v_tmpl_id AND parameter_id = v_param_mga;

    IF v_rel_mga IS NULL THEN
        INSERT INTO amunet_quality_parameter_product_rel
            (product_tmpl_id, parameter_id, parameter_code, display_name,
             active, sequence, active_spec_count,
             create_date, write_date, create_uid, write_uid)
        VALUES (v_tmpl_id, v_param_mga, 'MGA-0486', '[MGA-0486] MGA-0486',
                true, 20, 1, NOW(), NOW(), 1, 1)
        RETURNING id INTO v_rel_mga;
        RAISE NOTICE 'Rel MGA-0486 creada: %', v_rel_mga;
    ELSE
        UPDATE amunet_quality_parameter_product_rel
        SET active = true, sequence = 20, active_spec_count = 1, write_date = NOW()
        WHERE id = v_rel_mga;
        RAISE NOTICE 'Rel MGA-0486 ya existía: %', v_rel_mga;
    END IF;

    -- Spec_config para MGA-0486
    SELECT id INTO v_sc_mga
    FROM amunet_quality_parameter_specification_config
    WHERE product_parameter_rel_id = v_rel_mga AND specification_id = v_spec_colorante;

    IF v_sc_mga IS NULL THEN
        INSERT INTO amunet_quality_parameter_specification_config
            (product_parameter_rel_id, specification_id, specification_name, evaluation_type,
             active, sequence, product_tmpl_id, parameter_id,
             binary_option_pass, binary_option_fail,
             acceptance_criteria,
             create_date, write_date, create_uid, write_uid)
        VALUES (v_rel_mga, v_spec_colorante, 'Hermeticidad', 'binary_selection',
                true, 10, v_tmpl_id, v_param_mga,
                'Ausencia de colorante', 'Presencia de colorante',
                'Ausencia de colorante',
                NOW(), NOW(), 1, 1)
        RETURNING id INTO v_sc_mga;
        RAISE NOTICE 'Spec_config MGA-0486 creada: %', v_sc_mga;
    ELSE
        RAISE NOTICE 'Spec_config MGA-0486 ya existía: %', v_sc_mga;
    END IF;

    -- ========================================================
    -- PARTE 4: Crear rel + spec_config para INC-002
    -- ========================================================
    SELECT id INTO v_rel_inc
    FROM amunet_quality_parameter_product_rel
    WHERE product_tmpl_id = v_tmpl_id AND parameter_id = v_param_inc;

    IF v_rel_inc IS NULL THEN
        INSERT INTO amunet_quality_parameter_product_rel
            (product_tmpl_id, parameter_id, parameter_code, display_name,
             active, sequence, active_spec_count,
             create_date, write_date, create_uid, write_uid)
        VALUES (v_tmpl_id, v_param_inc, 'INC-002', '[INC-002] INC-002',
                true, 50, 1, NOW(), NOW(), 1, 1)
        RETURNING id INTO v_rel_inc;
        RAISE NOTICE 'Rel INC-002 creada: %', v_rel_inc;
    ELSE
        UPDATE amunet_quality_parameter_product_rel
        SET active = true, sequence = 50, active_spec_count = 1, write_date = NOW()
        WHERE id = v_rel_inc;
        RAISE NOTICE 'Rel INC-002 ya existía: %', v_rel_inc;
    END IF;

    -- Spec_config para INC-002
    SELECT id INTO v_sc_inc
    FROM amunet_quality_parameter_specification_config
    WHERE product_parameter_rel_id = v_rel_inc AND specification_id = v_spec_inc;

    IF v_sc_inc IS NULL THEN
        INSERT INTO amunet_quality_parameter_specification_config
            (product_parameter_rel_id, specification_id, specification_name, evaluation_type,
             active, sequence, product_tmpl_id, parameter_id,
             binary_option_pass, binary_option_fail,
             acceptance_criteria,
             create_date, write_date, create_uid, write_uid)
        VALUES (v_rel_inc, v_spec_inc, 'Verificación de contenido de empaque', 'binary_selection',
                true, 10, v_tmpl_id, v_param_inc,
                'Contenido coincide', 'Contenido no coincide',
                'Coincidencia con el contenido especificado en el manual vigente.',
                NOW(), NOW(), 1, 1)
        RETURNING id INTO v_sc_inc;
        RAISE NOTICE 'Spec_config INC-002 creada: %', v_sc_inc;
    ELSE
        RAISE NOTICE 'Spec_config INC-002 ya existía: %', v_sc_inc;
    END IF;

    -- ========================================================
    -- PARTE 5: Agregar test_lines + detalles al análisis 893
    -- ========================================================

    -- MGA-0486
    SELECT id INTO v_line_mga
    FROM amunet_quality_test_line
    WHERE check_id = v_check_id AND parameter_id = v_param_mga LIMIT 1;

    IF v_line_mga IS NULL THEN
        INSERT INTO amunet_quality_test_line
            (check_id, parameter_id, code, name, sequence, has_details, detail_count,
             create_date, write_date, create_uid, write_uid)
        VALUES (v_check_id, v_param_mga, 'MGA-0486', 'Hermeticidad',
                20, true, 1, NOW(), NOW(), 1, 1)
        RETURNING id INTO v_line_mga;
        RAISE NOTICE 'Test_line MGA-0486 creada: %', v_line_mga;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM amunet_quality_test_line_detail
        WHERE check_id = v_check_id AND test_line_id = v_line_mga
    ) THEN
        INSERT INTO amunet_quality_test_line_detail
            (check_id, test_line_id, name, evaluation_type,
             binary_option_pass, binary_option_fail,
             acceptance_criteria, expected_value_binary,
             sequence, specification_config_id, specification_id,
             verdict, create_date, write_date, create_uid, write_uid)
        VALUES (v_check_id, v_line_mga,
                'Prueba de colorante', 'binary_selection',
                'Ausencia de colorante', 'Presencia de colorante',
                'Ausencia de colorante', 'pass',
                1, v_sc_mga, v_spec_colorante,
                NULL, NOW(), NOW(), 1, 1);
        RAISE NOTICE 'Detalle MGA-0486 creado';
    END IF;

    -- INC-002
    SELECT id INTO v_line_inc
    FROM amunet_quality_test_line
    WHERE check_id = v_check_id AND parameter_id = v_param_inc LIMIT 1;

    IF v_line_inc IS NULL THEN
        INSERT INTO amunet_quality_test_line
            (check_id, parameter_id, code, name, sequence, has_details, detail_count,
             create_date, write_date, create_uid, write_uid)
        VALUES (v_check_id, v_param_inc, 'INC-002', 'Verificación de contenido de empaque',
                50, true, 1, NOW(), NOW(), 1, 1)
        RETURNING id INTO v_line_inc;
        RAISE NOTICE 'Test_line INC-002 creada: %', v_line_inc;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM amunet_quality_test_line_detail
        WHERE check_id = v_check_id AND test_line_id = v_line_inc
    ) THEN
        INSERT INTO amunet_quality_test_line_detail
            (check_id, test_line_id, name, evaluation_type,
             binary_option_pass, binary_option_fail,
             acceptance_criteria, expected_value_binary,
             sequence, specification_config_id, specification_id,
             verdict, create_date, write_date, create_uid, write_uid)
        VALUES (v_check_id, v_line_inc,
                'Verificación de contenido de empaque', 'binary_selection',
                'Contenido coincide', 'Contenido no coincide',
                'Coincidencia con el contenido especificado en el manual vigente.', 'pass',
                10, v_sc_inc, v_spec_inc,
                NULL, NOW(), NOW(), 1, 1);
        RAISE NOTICE 'Detalle INC-002 creado';
    END IF;

    -- ========================================================
    -- PARTE 6: Configurar el anexo del análisis 893
    -- ========================================================
    UPDATE amunet_quality_check
    SET
        anexo_titulo      = 'Anexo Producto Terminado Cartucho',
        tiene_anexos      = true,
        anexo_col1_header = 'Apariencia de Empaque',
        anexo_col2_header = 'Apariencia de Prueba',
        anexo_col3_header = 'Hermeticidad',
        anexo_col4_header = 'Contenido',
        anexo_col5_header = 'T. Liberación (seg)',
        anexo_col6_header = 'T. Migración (seg)',
        anexo_col7_header = 'Desempeño',
        anexo_col8_header = '',
        write_date = NOW()
    WHERE id = v_check_id;
    RAISE NOTICE 'Anexo configurado';

    -- ========================================================
    -- PARTE 7: Desactivar rels VAMA/MAVI-13 del producto
    --          (para que futuros análisis no los incluyan)
    -- ========================================================
    UPDATE amunet_quality_parameter_product_rel
    SET active = false, write_date = NOW()
    WHERE product_tmpl_id = v_tmpl_id
      AND parameter_id IN (
          SELECT id FROM amunet_quality_check_parameter
          WHERE code IN ('VAMA-034','VAMA-036','VAMA-064','VAMA-091','VAMA-038','VAMA-096','MAVI-13')
      );
    RAISE NOTICE 'Rels VAMA/MAVI-13 desactivadas';

    -- Desactivar spec "Interpretación de Líneas" de MAVI-07 para este producto
    UPDATE amunet_quality_parameter_specification_config
    SET active = false, write_date = NOW()
    WHERE product_parameter_rel_id = (
        SELECT r.id FROM amunet_quality_parameter_product_rel r
        WHERE r.product_tmpl_id = v_tmpl_id
          AND r.parameter_id = v_param_mavi07
        LIMIT 1
    ) AND specification_id IN (
        SELECT id FROM amunet_quality_check_parameter_specification
        WHERE parameter_id = v_param_mavi07 AND name ILIKE '%interpretaci%'
    );

    -- Actualizar active_spec_count de MAVI-07 (debe quedar en 2)
    UPDATE amunet_quality_parameter_product_rel
    SET active_spec_count = (
        SELECT COUNT(*) FROM amunet_quality_parameter_specification_config
        WHERE product_parameter_rel_id = amunet_quality_parameter_product_rel.id AND active = true
    ), sequence = 40, write_date = NOW()
    WHERE product_tmpl_id = v_tmpl_id AND parameter_id = v_param_mavi07;

    -- Limpiar exceso de specs MAVI-09 (dejar solo Liberación y Migración)
    UPDATE amunet_quality_parameter_specification_config
    SET active = false, write_date = NOW()
    WHERE product_parameter_rel_id = (
        SELECT r.id FROM amunet_quality_parameter_product_rel r
        WHERE r.product_tmpl_id = v_tmpl_id AND r.parameter_id = v_param_mavi09 LIMIT 1
    ) AND specification_id NOT IN (
        SELECT id FROM amunet_quality_check_parameter_specification
        WHERE parameter_id = v_param_mavi09
          AND name IN ('Liberación de conjugado', 'Migración de conjugado')
    );

    -- Actualizar active_spec_count y sequence de MAVI-09 (debe quedar en 2)
    UPDATE amunet_quality_parameter_product_rel
    SET active_spec_count = (
        SELECT COUNT(*) FROM amunet_quality_parameter_specification_config
        WHERE product_parameter_rel_id = amunet_quality_parameter_product_rel.id AND active = true
    ), sequence = 30, write_date = NOW()
    WHERE product_tmpl_id = v_tmpl_id AND parameter_id = v_param_mavi09;

    -- Actualizar sequence de MAVI-04
    UPDATE amunet_quality_parameter_product_rel
    SET sequence = 10, write_date = NOW()
    WHERE product_tmpl_id = v_tmpl_id
      AND parameter_id = (SELECT id FROM amunet_quality_check_parameter WHERE code='MAVI-04' AND name='Aspectos Visuales' LIMIT 1);

    RAISE NOTICE '=== Fix completado para análisis % ===', v_check_id;
END;
$$;

-- ================================================================
-- VERIFICACIÓN FINAL — compartir con Diana para confirmar
-- ================================================================
SELECT tl.sequence, tl.code, tl.name as linea, tl.has_details,
       tl.detail_count, tl.verdict,
       d.name as detalle, d.evaluation_type, d.binary_option_pass,
       d.min_value, d.max_value, d.verdict as det_verdict
FROM amunet_quality_test_line tl
LEFT JOIN amunet_quality_test_line_detail d ON d.test_line_id = tl.id
WHERE tl.check_id = 893
ORDER BY tl.sequence, d.sequence;
