-- ============================================================
-- CORRECCIÓN: Desactivar VAMA-xxx activos en catálogo de DL%
-- Base de datos: amunet_prod
-- Fecha: 2026-09-17
-- Solicitado por: Diana Flores — Control de Calidad
--
-- Los productos DM% ya tienen VAMA-xxx con active = false (correcto).
-- Los siguientes DL% aún los tienen con active = true:
--   DLBIO01: VAMA-034, VAMA-036, VAMA-064, VAMA-091
--   DLLFS01: VAMA-034, VAMA-036, VAMA-038, VAMA-064, VAMA-091, VAMA-096
--   DLVPH01: VAMA-034, VAMA-036, VAMA-038, VAMA-064, VAMA-091, VAMA-096
--
-- Referencia correcta: DMTOR02 (ToRCH) — VAMA-xxx con active = false,
-- solo MAVI-04, MGA-0486, MAVI-09, MAVI-07 (vama_multi_check), INC-002 activos.
-- ============================================================

BEGIN;

UPDATE amunet_quality_parameter_product_rel
SET active = false, write_date = NOW()
WHERE id IN (
    -- DLBIO01
    3302,  -- VAMA-034
    3303,  -- VAMA-036
    3304,  -- VAMA-064
    3305,  -- VAMA-091
    -- DLLFS01
    4123,  -- VAMA-034
    4124,  -- VAMA-064
    4125,  -- VAMA-036
    4126,  -- VAMA-091
    4127,  -- VAMA-038
    4128,  -- VAMA-096
    -- DLVPH01
    3177,  -- VAMA-034
    3178,  -- VAMA-064
    3179,  -- VAMA-036
    3180,  -- VAMA-091
    3181,  -- VAMA-038
    3182   -- VAMA-096
);

COMMIT;

-- Verificación post-ejecución:
-- SELECT pp.default_code, qcp.code, rel.active
-- FROM amunet_quality_parameter_product_rel rel
-- JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id
-- JOIN product_template pt ON pt.id = rel.product_tmpl_id
-- JOIN product_product pp ON pp.product_tmpl_id = pt.id
-- WHERE pp.default_code IN ('DLBIO01','DLLFS01','DLVPH01')
--   AND qcp.code ILIKE 'VAMA%'
-- ORDER BY pp.default_code, qcp.code;
-- Resultado esperado: active = false en todos los registros.
