-- ============================================================
-- CORRECCIÓN: MAVI-07 evaluation_type mavi_07_ternary → vama_multi_check
-- para todos los productos PT cualitativos (DM/DL/DIAM/DRAM/DEMAM)
--
-- Base de datos: amunet_prod
-- Solicitado por: Diana Flores — Control de Calidad
-- Fecha: 2026-09-22
--
-- Contexto:
--   Los análisis cualitativos de producto terminado (DM*, DL*, DIAM*, DRAM*, DEMAM*)
--   deben usar evaluation_type = 'vama_multi_check' para los specs de MAVI-07
--   (Muestra negativa / Muestra positiva). El tipo 'mavi_07_ternary' es exclusivo
--   de Hojas Maestras (SPHMC/SPHMT) y mostraba un widget JSON ilegible en PT.
--
-- Impacto esperado: ~136 registros en la configuración raíz de especificaciones.
-- ============================================================

BEGIN;

UPDATE amunet_quality_parameter_specification_config aqcpsc
SET evaluation_type = 'vama_multi_check',
    write_date      = NOW()
FROM amunet_quality_check_parameter aqcp,
     product_template pt
WHERE aqcp.id = aqcpsc.parameter_id
  AND pt.id   = aqcpsc.product_tmpl_id
  AND aqcp.code = 'MAVI-07'
  AND aqcpsc.evaluation_type = 'mavi_07_ternary'
  AND aqcpsc.active = true
  AND (
       pt.default_code ILIKE 'DM%'
    OR pt.default_code ILIKE 'DL%'
    OR pt.default_code ILIKE 'DIAM%'
    OR pt.default_code ILIKE 'DRAM%'
    OR pt.default_code ILIKE 'DEMAM%'
  );

-- Verificación post-ejecución (descomentar para revisar):
-- SELECT COUNT(*) FROM amunet_quality_parameter_specification_config aqcpsc
-- JOIN amunet_quality_check_parameter aqcp ON aqcp.id = aqcpsc.parameter_id
-- JOIN product_template pt ON pt.id = aqcpsc.product_tmpl_id
-- WHERE aqcp.code = 'MAVI-07' AND aqcpsc.evaluation_type = 'mavi_07_ternary'
--   AND aqcpsc.active = true
--   AND (pt.default_code ILIKE 'DM%' OR pt.default_code ILIKE 'DL%');
-- Resultado esperado: 0

COMMIT;
