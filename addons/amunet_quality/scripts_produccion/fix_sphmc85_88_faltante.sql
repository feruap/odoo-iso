-- ============================================================
-- SCRIPT CORRECTIVO: SPHMC85-88 — lo que faltó del v2
-- Preparado: 2026-09-30 | Aplicar en amunet_prod
-- ============================================================
-- Contexto: el script fix_sphmc85_88_v2_seguro.sql se aplicó
-- parcialmente el 2026-09-29. Quedaron pendientes:
--   1. INSERT de 3 MAVI-04 activos (Manchas, Rasgaduras, Deformidad)
--      copiados de SPHMC62 — los 4 productos tienen 0 activos
--   2. UPDATE de "Vial - Altura" a seq=99 en MAVI-11
--      (IDs 86943, 87075, 87207, 87339 — verificados en producción)
-- Lo que SÍ quedó bien en el v2: MAVI-09 criterios y análisis QC/00503-505
-- ============================================================

BEGIN;

-- ============================================================
-- PARTE 1: Agregar MAVI-04 activos (copia de SPHMC62)
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
JOIN amunet_quality_parameter_product_rel new_ppr ON new_ppr.parameter_id = ref_ppr.parameter_id
JOIN product_template new_pt ON new_pt.id = new_ppr.product_tmpl_id
WHERE ref_pt.default_code = 'SPHMC62'
  AND cp.code = 'MAVI-04'
  AND ref.sequence < 99
  AND new_pt.default_code IN ('SPHMC85','SPHMC86','SPHMC87','SPHMC88')
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config e
    WHERE e.product_parameter_rel_id = new_ppr.id
      AND e.specification_name = ref.specification_name
      AND e.sequence < 99
  );
-- Esperado: INSERT 0 12

-- ============================================================
-- PARTE 2: Archivar "Vial - Altura" en MAVI-11
-- ============================================================

UPDATE amunet_quality_parameter_specification_config
SET sequence = 99, write_date = NOW()
WHERE id IN (86943, 87075, 87207, 87339)
  AND specification_name = 'Vial - Altura';
-- Esperado: UPDATE 4

-- ============================================================
-- VERIFICACIÓN
-- ============================================================

SELECT pt.default_code,
  COUNT(psc.id) FILTER (WHERE cp.code='MAVI-04' AND psc.sequence < 99) as m04,
  COUNT(psc.id) FILTER (WHERE cp.code='MAVI-11' AND psc.sequence < 99) as m11
FROM product_template pt
JOIN amunet_quality_parameter_product_rel ppr ON ppr.product_tmpl_id = pt.id
JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
LEFT JOIN amunet_quality_parameter_specification_config psc ON psc.product_parameter_rel_id = ppr.id
WHERE pt.default_code IN ('SPHMC85','SPHMC86','SPHMC87','SPHMC88')
  AND cp.code IN ('MAVI-04','MAVI-11')
GROUP BY pt.default_code ORDER BY pt.default_code;
-- Debe mostrar: m04=3, m11=1 para los 4 productos

COMMIT;
