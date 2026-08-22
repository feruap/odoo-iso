-- CORRECCIÓN URGENTE: SPHMC75 y SPHMC76 — puntos de control QC
-- Aprobado por: Diana Flores (Calidad)
-- Fuente: spec configs de SPHMC53 (rels 72793-72799) y SPHMC54 (72800-72806)
-- SPHMC53/54 NO SE TOCAN — solo se copian sus configuraciones
-- Ejecutar en: amunet_prod
-- Fecha: 2026-08-07

BEGIN;

-- 1. Eliminar TLDs que referencien specs erróneos de SPHMC75/76 (si hay checks abiertos)
DELETE FROM amunet_quality_test_line_detail
WHERE specification_config_id IN (
    SELECT id FROM amunet_quality_parameter_specification_config
    WHERE product_parameter_rel_id IN (3186,3189,3190,3187,3192,3193)
);

-- 2. Eliminar specs duplicados/erróneos de SPHMC75 (MAVI-04/09/11) y SPHMC76 (MAVI-04/09/11)
--    MAVI-07 (rels 3188/3191) NO se toca — ya tiene las 2 specs correctas
DELETE FROM amunet_quality_parameter_specification_config
WHERE product_parameter_rel_id IN (3186,3189,3190,3187,3192,3193);

-- 3. Copiar specs de SPHMC53 → SPHMC75 (rels 3186/3189/3190)
INSERT INTO amunet_quality_parameter_specification_config
  (product_parameter_rel_id, specification_id, sequence, uom_id, specification_name, evaluation_type,
   acceptance_criteria, binary_prefix, binary_suffix, binary_expected_option, binary_option_pass, binary_option_fail,
   checkbox_label_1, checkbox_label_2, text_pattern_expected, text_pattern_regex, expected_options, obtained_options,
   binary_notes_option_pass, binary_notes_option_fail, ternary_option_yes, ternary_option_no, ternary_option_na,
   text_phrase_mapping, nominal_value, tolerance, min_value, max_value, min_value_manual, max_value_manual,
   active, use_manual_range, checkbox_require_both, binary_notes_required, create_uid, write_uid, create_date, write_date)
SELECT
  CASE ref.parameter_code
    WHEN 'MAVI-04' THEN 3186
    WHEN 'MAVI-09' THEN 3189
    WHEN 'MAVI-11' THEN 3190
  END,
  sc.specification_id, sc.sequence, sc.uom_id, sc.specification_name, sc.evaluation_type,
  sc.acceptance_criteria, sc.binary_prefix, sc.binary_suffix, sc.binary_expected_option,
  sc.binary_option_pass, sc.binary_option_fail, sc.checkbox_label_1, sc.checkbox_label_2,
  sc.text_pattern_expected, sc.text_pattern_regex, sc.expected_options, sc.obtained_options,
  sc.binary_notes_option_pass, sc.binary_notes_option_fail, sc.ternary_option_yes, sc.ternary_option_no, sc.ternary_option_na,
  sc.text_phrase_mapping, sc.nominal_value, sc.tolerance, sc.min_value, sc.max_value,
  sc.min_value_manual, sc.max_value_manual, TRUE, sc.use_manual_range, sc.checkbox_require_both,
  sc.binary_notes_required, 1, 1, NOW(), NOW()
FROM amunet_quality_parameter_specification_config sc
JOIN amunet_quality_parameter_product_rel ref ON ref.id = sc.product_parameter_rel_id
WHERE sc.id IN (72793,72794,72795,72796,72797,72799);

-- 4. Copiar specs de SPHMC54 → SPHMC76 (rels 3187/3192/3193)
INSERT INTO amunet_quality_parameter_specification_config
  (product_parameter_rel_id, specification_id, sequence, uom_id, specification_name, evaluation_type,
   acceptance_criteria, binary_prefix, binary_suffix, binary_expected_option, binary_option_pass, binary_option_fail,
   checkbox_label_1, checkbox_label_2, text_pattern_expected, text_pattern_regex, expected_options, obtained_options,
   binary_notes_option_pass, binary_notes_option_fail, ternary_option_yes, ternary_option_no, ternary_option_na,
   text_phrase_mapping, nominal_value, tolerance, min_value, max_value, min_value_manual, max_value_manual,
   active, use_manual_range, checkbox_require_both, binary_notes_required, create_uid, write_uid, create_date, write_date)
SELECT
  CASE ref.parameter_code
    WHEN 'MAVI-04' THEN 3187
    WHEN 'MAVI-09' THEN 3192
    WHEN 'MAVI-11' THEN 3193
  END,
  sc.specification_id, sc.sequence, sc.uom_id, sc.specification_name, sc.evaluation_type,
  sc.acceptance_criteria, sc.binary_prefix, sc.binary_suffix, sc.binary_expected_option,
  sc.binary_option_pass, sc.binary_option_fail, sc.checkbox_label_1, sc.checkbox_label_2,
  sc.text_pattern_expected, sc.text_pattern_regex, sc.expected_options, sc.obtained_options,
  sc.binary_notes_option_pass, sc.binary_notes_option_fail, sc.ternary_option_yes, sc.ternary_option_no, sc.ternary_option_na,
  sc.text_phrase_mapping, sc.nominal_value, sc.tolerance, sc.min_value, sc.max_value,
  sc.min_value_manual, sc.max_value_manual, TRUE, sc.use_manual_range, sc.checkbox_require_both,
  sc.binary_notes_required, 1, 1, NOW(), NOW()
FROM amunet_quality_parameter_specification_config sc
JOIN amunet_quality_parameter_product_rel ref ON ref.id = sc.product_parameter_rel_id
WHERE sc.id IN (72800,72801,72802,72803,72804,72806);

-- Verificación final
SELECT pp.default_code, rel.parameter_code, COUNT(sc.id) as specs_activas
FROM product_product pp
JOIN product_template pt ON pt.id = pp.product_tmpl_id
JOIN amunet_quality_parameter_product_rel rel ON rel.product_tmpl_id = pt.id
JOIN amunet_quality_parameter_specification_config sc ON sc.product_parameter_rel_id = rel.id AND sc.active = TRUE
WHERE pp.default_code IN ('SPHMC75','SPHMC76')
GROUP BY pp.default_code, rel.parameter_code
ORDER BY pp.default_code, rel.parameter_code;

-- Si la verificación muestra 3,2,2,1 para cada producto → COMMIT
-- Si algo falla → ROLLBACK
COMMIT;
