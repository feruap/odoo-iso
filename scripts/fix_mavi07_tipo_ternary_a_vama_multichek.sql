-- ============================================================
-- CORRECCIÓN: MAVI-07 tipo mavi_07_ternary y mavi_07 → vama_multi_check
-- Base de datos: amunet_prod
-- Fecha: 2026-09-18
-- Solicitado por: Diana Flores — Control de Calidad
--
-- Problema: varios productos PT, HM y buffers tienen MAVI-07
-- con evaluation_type = 'mavi_07_ternary' o 'mavi_07' (tipos
-- incorrectos). El tipo correcto es 'vama_multi_check', que es
-- el que usa el resto del catálogo.
--
-- Productos afectados (60 spec_configs, 30 productos):
--   Pruebas cualitativas: DIAM-002/023/024/025/029, DEMAM-001,
--     DMROT01, DMZNS01, AMU-82157, DMCOC02, DMTHC02, DMOPOI02,
--     y productos sin código numérico (Lactoferrina, Filariasis,
--     Brucella, Lyme, Clostridium difficile)
--   Antidoping: DMACT02, DMADO03, DMADO04, DMAMP02, DMMET02,
--     DMOPI02, DMOPI02, DMDRO01
--   Buffers: STBCH01, STBDN01, STBHB01, STBPR02
--   Reactivos: STREX01, STREX02
--
-- NOTA: Este script cambia solo el evaluation_type.
-- Los expected_options (patrones de resultado) deben revisarse
-- por separado: ver fix_mavi07_expected_options.sql
-- ============================================================

BEGIN;

UPDATE amunet_quality_parameter_specification_config sc
SET evaluation_type = 'vama_multi_check',
    write_date = NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id
WHERE sc.product_parameter_rel_id = rel.id
  AND rel.active = true
  AND qcp.code = 'MAVI-07'
  AND sc.evaluation_type IN ('mavi_07_ternary', 'mavi_07');

COMMIT;

-- ── Verificación post-ejecución ───────────────────────────────────────────────
-- No debe arrojar filas (todos deben quedar en vama_multi_check):
--
-- SELECT pp.default_code, sc.evaluation_type, sc.expected_options
-- FROM product_product pp
-- JOIN product_template pt ON pt.id = pp.product_tmpl_id
-- JOIN amunet_quality_parameter_product_rel rel ON rel.product_tmpl_id = pt.id AND rel.active=true
-- JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code='MAVI-07'
-- JOIN amunet_quality_parameter_specification_config sc ON sc.product_parameter_rel_id = rel.id
-- WHERE sc.evaluation_type IN ('mavi_07_ternary', 'mavi_07');
