-- ============================================================
-- CORRECCIÓN: Agregar expected_options a MAVI-07 vama_multi_check
-- Base de datos: amunet_prod
-- Fecha: 2026-09-17
-- Solicitado por: Diana Flores — Control de Calidad
--
-- El widget vama_multi_check necesita expected_options para mostrar
-- las líneas seleccionables. Sin este campo el analista no puede
-- seleccionar nada en el MAVI-07 y el análisis queda bloqueado.
--
-- Afecta DOS lugares:
--   1. El CATÁLOGO (spec_configs): para que nuevos análisis nazcan bien.
--   2. Los ANÁLISIS ACTIVOS (draft/in_progress): para desbloquear los
--      que ya están abiertos (199 detalles en ~120 análisis).
-- ============================================================

BEGIN;

-- ── 1. CATÁLOGO ──────────────────────────────────────────────────────────────
UPDATE amunet_quality_parameter_specification_config
SET expected_options = 'Positiva, Negativa',
    write_date = NOW()
WHERE evaluation_type = 'vama_multi_check'
  AND (expected_options IS NULL OR expected_options = '');

-- ── 2. ANÁLISIS ACTIVOS (draft + in_progress) ────────────────────────────────
UPDATE amunet_quality_test_line_detail tld
SET expected_options = 'Positiva, Negativa',
    write_date = NOW()
FROM amunet_quality_check qc
WHERE tld.check_id = qc.id
  AND tld.evaluation_type = 'vama_multi_check'
  AND (tld.expected_options IS NULL OR tld.expected_options = '')
  AND qc.state IN ('draft', 'in_progress');

COMMIT;

-- Verificación rápida post-ejecución:
-- SELECT COUNT(*) FROM amunet_quality_parameter_specification_config
-- WHERE evaluation_type = 'vama_multi_check'
--   AND (expected_options IS NULL OR expected_options = '');
-- Debe devolver 0.
--
-- SELECT COUNT(*) FROM amunet_quality_test_line_detail tld
-- JOIN amunet_quality_check qc ON qc.id = tld.check_id
-- WHERE tld.evaluation_type = 'vama_multi_check'
--   AND (tld.expected_options IS NULL OR tld.expected_options = '')
--   AND qc.state IN ('draft','in_progress');
-- Debe devolver 0.
