-- ============================================================
-- CORRECCIÓN: MAVI-07 criterios de aceptación en Competitivas
-- Base de datos: amunet_prod
-- Fecha: 2026-09-21
-- Solicitado por: Diana Flores — Control de Calidad
--
-- Problema: los productos Competitivos tienen el patrón de
-- líneas (#5 y #1-4) pero sin la etiqueta descriptiva en el
-- campo acceptance_criteria. Las Cualitativas ya la tienen.
--
-- Productos afectados (Grupo F):
--   DRAM-002  (Albúmina Cualitativa)
--   DMFEN01   (Fentanilo)
--   DMADB01   (Antidoping Saliva 5P)
--   DMADO02   (Antidoping Orina 5P — tira)
--   DMDRO01   (Drogs Net)
--
-- Corrección: añadir texto descriptivo a acceptance_criteria,
-- igual al formato de las Cualitativas (DMVIH01, DMHCG01, etc.)
--   Muestra negativa  → "Visualización solo de línea control, patrón #5"
--   Muestra positiva  → "Visualización línea control y línea de prueba, patrón #1, #2, #3 y #4"
-- ============================================================

BEGIN;

-- Muestra negativa (spec_ids: 89304, 89315, 85417, 89568, 89964)
UPDATE amunet_quality_parameter_specification_config
SET acceptance_criteria = 'Visualización solo de línea control, patrón #5',
    write_date = NOW()
WHERE id IN (89304, 89315, 85417, 89568, 89964)
  AND specification_name = 'Muestra negativa';

-- Muestra positiva (spec_ids: 89305, 89316, 85418, 89569, 89965)
UPDATE amunet_quality_parameter_specification_config
SET acceptance_criteria = 'Visualización línea control y línea de prueba, patrón #1, #2, #3 y #4',
    write_date = NOW()
WHERE id IN (89305, 89316, 85418, 89569, 89965)
  AND specification_name = 'Muestra positiva';

COMMIT;

-- ── Verificación ─────────────────────────────────────────────────────────────
-- SELECT pp.default_code, sc.specification_name, sc.acceptance_criteria
-- FROM product_product pp
-- JOIN product_template pt ON pt.id = pp.product_tmpl_id
-- JOIN amunet_quality_parameter_product_rel rel ON rel.product_tmpl_id = pt.id AND rel.active=true
-- JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code='MAVI-07'
-- JOIN amunet_quality_parameter_specification_config sc ON sc.product_parameter_rel_id = rel.id AND sc.active=true
-- WHERE pp.default_code IN ('DRAM-002','DMFEN01','DMADB01','DMDRO01','DMADO02')
-- ORDER BY pp.default_code, sc.sequence;
