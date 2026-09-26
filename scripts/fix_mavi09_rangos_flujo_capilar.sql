-- ============================================================
-- CORRECCIÓN: Rangos de flujo capilar MAVI-09
-- Base de datos: amunet_prod
-- Fecha: 2026-09-18
-- Solicitado por: Diana Flores — Control de Calidad
--
-- MAVI-09 registra tiempos de flujo capilar (no dimensiones físicas).
-- Los spec_configs con evaluation_type='numeric_range' y min/max NULL
-- deben tener:
--   Liberación (de conjugado / Tiempo de liberación): min=1  max=30  (segundos)
--   Migración  (de conjugado / Tiempo de migración):  min=30 max=180 (segundos)
--
-- Productos afectados (20 especificaciones en 10 productos):
--   PT cualitativas:   DMHPY01, DMPSA02
--   Hojas maestras:    SPHMT07, SPHMT08, SPHMT09, SPHMT10, SPHMT11, SPHMT12
--   Buffer (revisar):  STBPR04  ← confirmar si aplica el mismo rango
-- ============================================================

BEGIN;

-- ── Liberación (Liberación de conjugado / Tiempo de liberación) ──────────────
UPDATE amunet_quality_parameter_specification_config sc
SET min_value  = 1,
    max_value  = 30,
    write_date = NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id
WHERE sc.product_parameter_rel_id = rel.id
  AND rel.active = true
  AND qcp.code = 'MAVI-09'
  AND sc.evaluation_type = 'numeric_range'
  AND (sc.min_value IS NULL OR sc.max_value IS NULL)
  AND sc.specification_name ILIKE '%liberac%';

-- ── Migración (Migración de conjugado / Tiempo de migración) ─────────────────
UPDATE amunet_quality_parameter_specification_config sc
SET min_value  = 30,
    max_value  = 180,
    write_date = NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id
WHERE sc.product_parameter_rel_id = rel.id
  AND rel.active = true
  AND qcp.code = 'MAVI-09'
  AND sc.evaluation_type = 'numeric_range'
  AND (sc.min_value IS NULL OR sc.max_value IS NULL)
  AND sc.specification_name ILIKE '%migraci%';

COMMIT;

-- Verificación post-ejecución:
-- SELECT pp.default_code, sc.specification_name, sc.min_value, sc.max_value
-- FROM product_product pp
-- JOIN product_template pt ON pt.id = pp.product_tmpl_id
-- JOIN amunet_quality_parameter_product_rel rel ON rel.product_tmpl_id = pt.id
-- JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id
-- JOIN amunet_quality_parameter_specification_config sc ON sc.product_parameter_rel_id = rel.id
-- WHERE rel.active = true AND qcp.code = 'MAVI-09'
--   AND sc.evaluation_type = 'numeric_range'
--   AND sc.specification_name ILIKE '%liberac%' OR sc.specification_name ILIKE '%migraci%'
-- ORDER BY pp.default_code, sc.specification_name;
-- Resultado esperado: Liberación=1-30, Migración=30-180 en todos.
