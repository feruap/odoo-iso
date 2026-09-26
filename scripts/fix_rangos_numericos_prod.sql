-- ============================================================
-- CORRECCIÓN: Rangos numéricos en cero en análisis de producción
-- Base de datos: amunet_prod
-- Fecha: 2026-09-11
-- Solicitado por: Diana Flores — Control de Calidad
--
-- El catálogo (spec_config) tiene los rangos correctos, pero
-- cuando se generaron los detalles de los análisis, los valores
-- min_value/max_value no se copiaron. Este script los corrige
-- directamente en cada detalle afectado.
--
-- ANÁLISIS AFECTADOS:
--   PT Cartuchos: DMCAO01 (CA125, id=894), DMZIK01 (Zika, id=896)
--   Hojas Maestras: SPHMT06 (id=546), SPHMT04 (id=572)
--   Buffers: MPADE01 (ids=455,726), MPABI01 (ids=456,727), MPATR01 (ids=457,728)
-- ============================================================

BEGIN;

-- ── PT CARTUCHOS: MAVI-09 Liberación (1-30s) y Migración (30-180s) ──────────

-- CA125 (análisis 894)
UPDATE amunet_quality_test_line_detail
SET min_value = 1, max_value = 30, write_date = NOW()
WHERE id = 7993; -- Liberación de conjugado

UPDATE amunet_quality_test_line_detail
SET min_value = 30, max_value = 180, write_date = NOW()
WHERE id = 7994; -- Migración de conjugado

-- Zika (análisis 896)
UPDATE amunet_quality_test_line_detail
SET min_value = 1, max_value = 30, write_date = NOW()
WHERE id = 8055; -- Liberación de conjugado

UPDATE amunet_quality_test_line_detail
SET min_value = 30, max_value = 180, write_date = NOW()
WHERE id = 8056; -- Migración de conjugado

-- ── HOJAS MAESTRAS: MAVI-09 Tiempo de liberación (1-30s) ────────────────────

-- SPHMT06 (análisis 546)
UPDATE amunet_quality_test_line_detail
SET min_value = 1, max_value = 30, write_date = NOW()
WHERE id = 3195; -- Tiempo de liberación

-- SPHMT04 (análisis 572)
UPDATE amunet_quality_test_line_detail
SET min_value = 1, max_value = 30, write_date = NOW()
WHERE id = 3424; -- Tiempo de liberación

COMMIT;

-- ── Verificación post-ejecución (correr por separado) ───────────────────────
-- SELECT tld.id, qc.name, pp.default_code, tl.code, tld.name,
--        tld.min_value, tld.max_value
-- FROM amunet_quality_test_line_detail tld
-- JOIN amunet_quality_test_line tl ON tl.id = tld.test_line_id
-- JOIN amunet_quality_check qc ON qc.id = tl.check_id
-- JOIN product_product pp ON pp.id = qc.product_id
-- WHERE tld.id IN (7993,7994,8055,8056,3195,3424,2541,2546,2551,4915,4920,4925)
-- ORDER BY qc.id, tl.sequence, tld.id;
