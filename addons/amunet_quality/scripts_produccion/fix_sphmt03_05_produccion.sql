-- ============================================================
-- SCRIPT: SPHMT03-05 — Configuración completa desde raíz
-- (VPH, Pylorinet, TB-DxNet — variantes activas creadas 2026-09-23)
-- Ejecutar en amunet_prod, por Fernando/desarrollo
-- Validado: 31 spec_configs a copiar, 12 ppr a crear, 3 QP a asignar
-- ============================================================

BEGIN;

-- ============================================================
-- PASO 1: Crear 12 product_parameter_rel para las nuevas plantillas
-- (4 params × 3 productos = 12 registros)
-- ============================================================

INSERT INTO amunet_quality_parameter_product_rel
  (product_tmpl_id, parameter_id, sequence, active, create_uid, write_uid, create_date, write_date)
SELECT new_tmpl, old_ppr.parameter_id, old_ppr.sequence, true, 1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel old_ppr
JOIN (VALUES (1507, 2377), (1508, 2378), (1509, 2379)) AS m(old_tmpl, new_tmpl)
  ON old_ppr.product_tmpl_id = m.old_tmpl
WHERE old_ppr.parameter_id IN (1, 65, 69, 64)
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_product_rel x
    WHERE x.product_tmpl_id = m.new_tmpl AND x.parameter_id = old_ppr.parameter_id
  );

-- ============================================================
-- PASO 2: Copiar 31 spec_configs de archivadas → nuevas
-- (idempotente por nombre de spec dentro del mismo parámetro)
-- ============================================================

-- SPHMT03 (1507 → 2377)
INSERT INTO amunet_quality_parameter_specification_config (
  product_parameter_rel_id, specification_id, sequence, uom_id,
  product_tmpl_id, parameter_id, company_id,
  specification_name, evaluation_type, acceptance_criteria,
  binary_prefix, binary_suffix, binary_expected_option, binary_option_pass, binary_option_fail,
  checkbox_label_1, checkbox_label_2, text_pattern_expected, text_pattern_regex,
  expected_options, obtained_options, binary_notes_option_pass, binary_notes_option_fail,
  ternary_option_yes, ternary_option_no, ternary_option_na,
  range_display, config_summary, text_phrase_mapping,
  nominal_value, tolerance, min_value, max_value,
  create_uid, write_uid, create_date, write_date
)
SELECT
  new_ppr.id, psc.specification_id, psc.sequence, psc.uom_id,
  2377, psc.parameter_id, psc.company_id,
  psc.specification_name, psc.evaluation_type, psc.acceptance_criteria,
  psc.binary_prefix, psc.binary_suffix, psc.binary_expected_option, psc.binary_option_pass, psc.binary_option_fail,
  psc.checkbox_label_1, psc.checkbox_label_2, psc.text_pattern_expected, psc.text_pattern_regex,
  psc.expected_options, psc.obtained_options, psc.binary_notes_option_pass, psc.binary_notes_option_fail,
  psc.ternary_option_yes, psc.ternary_option_no, psc.ternary_option_na,
  psc.range_display, psc.config_summary, psc.text_phrase_mapping,
  psc.nominal_value, psc.tolerance, psc.min_value, psc.max_value,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_specification_config psc
JOIN amunet_quality_parameter_product_rel old_ppr ON old_ppr.id = psc.product_parameter_rel_id
JOIN amunet_quality_parameter_product_rel new_ppr
  ON new_ppr.product_tmpl_id = 2377 AND new_ppr.parameter_id = old_ppr.parameter_id
WHERE old_ppr.product_tmpl_id = 1507;

-- SPHMT04 (1508 → 2378)
INSERT INTO amunet_quality_parameter_specification_config (
  product_parameter_rel_id, specification_id, sequence, uom_id,
  product_tmpl_id, parameter_id, company_id,
  specification_name, evaluation_type, acceptance_criteria,
  binary_prefix, binary_suffix, binary_expected_option, binary_option_pass, binary_option_fail,
  checkbox_label_1, checkbox_label_2, text_pattern_expected, text_pattern_regex,
  expected_options, obtained_options, binary_notes_option_pass, binary_notes_option_fail,
  ternary_option_yes, ternary_option_no, ternary_option_na,
  range_display, config_summary, text_phrase_mapping,
  nominal_value, tolerance, min_value, max_value,
  create_uid, write_uid, create_date, write_date
)
SELECT
  new_ppr.id, psc.specification_id, psc.sequence, psc.uom_id,
  2378, psc.parameter_id, psc.company_id,
  psc.specification_name, psc.evaluation_type, psc.acceptance_criteria,
  psc.binary_prefix, psc.binary_suffix, psc.binary_expected_option, psc.binary_option_pass, psc.binary_option_fail,
  psc.checkbox_label_1, psc.checkbox_label_2, psc.text_pattern_expected, psc.text_pattern_regex,
  psc.expected_options, psc.obtained_options, psc.binary_notes_option_pass, psc.binary_notes_option_fail,
  psc.ternary_option_yes, psc.ternary_option_no, psc.ternary_option_na,
  psc.range_display, psc.config_summary, psc.text_phrase_mapping,
  psc.nominal_value, psc.tolerance, psc.min_value, psc.max_value,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_specification_config psc
JOIN amunet_quality_parameter_product_rel old_ppr ON old_ppr.id = psc.product_parameter_rel_id
JOIN amunet_quality_parameter_product_rel new_ppr
  ON new_ppr.product_tmpl_id = 2378 AND new_ppr.parameter_id = old_ppr.parameter_id
WHERE old_ppr.product_tmpl_id = 1508;

-- SPHMT05 (1509 → 2379)
INSERT INTO amunet_quality_parameter_specification_config (
  product_parameter_rel_id, specification_id, sequence, uom_id,
  product_tmpl_id, parameter_id, company_id,
  specification_name, evaluation_type, acceptance_criteria,
  binary_prefix, binary_suffix, binary_expected_option, binary_option_pass, binary_option_fail,
  checkbox_label_1, checkbox_label_2, text_pattern_expected, text_pattern_regex,
  expected_options, obtained_options, binary_notes_option_pass, binary_notes_option_fail,
  ternary_option_yes, ternary_option_no, ternary_option_na,
  range_display, config_summary, text_phrase_mapping,
  nominal_value, tolerance, min_value, max_value,
  create_uid, write_uid, create_date, write_date
)
SELECT
  new_ppr.id, psc.specification_id, psc.sequence, psc.uom_id,
  2379, psc.parameter_id, psc.company_id,
  psc.specification_name, psc.evaluation_type, psc.acceptance_criteria,
  psc.binary_prefix, psc.binary_suffix, psc.binary_expected_option, psc.binary_option_pass, psc.binary_option_fail,
  psc.checkbox_label_1, psc.checkbox_label_2, psc.text_pattern_expected, psc.text_pattern_regex,
  psc.expected_options, psc.obtained_options, psc.binary_notes_option_pass, psc.binary_notes_option_fail,
  psc.ternary_option_yes, psc.ternary_option_no, psc.ternary_option_na,
  psc.range_display, psc.config_summary, psc.text_phrase_mapping,
  psc.nominal_value, psc.tolerance, psc.min_value, psc.max_value,
  1, 1, NOW(), NOW()
FROM amunet_quality_parameter_specification_config psc
JOIN amunet_quality_parameter_product_rel old_ppr ON old_ppr.id = psc.product_parameter_rel_id
JOIN amunet_quality_parameter_product_rel new_ppr
  ON new_ppr.product_tmpl_id = 2379 AND new_ppr.parameter_id = old_ppr.parameter_id
WHERE old_ppr.product_tmpl_id = 1509;

-- ============================================================
-- PASO 3: Asignar puntos de control a las variantes activas
-- ============================================================

INSERT INTO amunet_quality_point_product_product_rel
  (amunet_quality_point_id, product_product_id)
SELECT qp_id, var_id
FROM (VALUES (308, 2201), (309, 2202), (310, 2203)) AS t(qp_id, var_id)
WHERE NOT EXISTS (
  SELECT 1 FROM amunet_quality_point_product_product_rel r
  WHERE r.amunet_quality_point_id = t.qp_id AND r.product_product_id = t.var_id
);

-- ============================================================
-- VERIFICACIÓN FINAL — debe devolver 31 filas
-- ============================================================
SELECT pt.default_code, cp.code as param, COUNT(psc.id) as specs
FROM product_template pt
JOIN amunet_quality_parameter_product_rel ppr ON ppr.product_tmpl_id = pt.id
JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
JOIN amunet_quality_parameter_specification_config psc ON psc.product_parameter_rel_id = ppr.id
WHERE pt.id IN (2377, 2378, 2379)
GROUP BY pt.default_code, cp.code
ORDER BY pt.default_code, cp.code;

COMMIT;
