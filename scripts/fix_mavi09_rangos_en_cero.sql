-- ============================================================
-- CORRECCIÓN: MAVI-09 con rangos en 0-0 (no en NULL)
-- Base de datos: amunet_prod
-- Fecha: 2026-09-21
-- Solicitado por: Diana Flores — Control de Calidad
--
-- El script anterior (fix_mavi09_rangos_flujo_capilar.sql) solo
-- tocó los registros con min/max en NULL. Quedaron 36 specs en
-- 34 productos con los rangos en 0.0-0.0, que evalúan MAL.
--
-- Corrección:
--   Liberación: min=1, max=30  (segundos)
--   Migración:  min=30, max=180 (segundos)
-- ============================================================

BEGIN;

-- Liberación (min=1, max=30)
UPDATE amunet_quality_parameter_specification_config sc
SET min_value = 1,
    max_value = 30,
    write_date = NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id
WHERE sc.product_parameter_rel_id = rel.id
  AND rel.active = true
  AND qcp.code = 'MAVI-09'
  AND sc.evaluation_type = 'numeric_range'
  AND sc.min_value = 0
  AND sc.max_value = 0
  AND sc.specification_name ILIKE '%liberac%';

-- Migración (min=30, max=180)
UPDATE amunet_quality_parameter_specification_config sc
SET min_value = 30,
    max_value = 180,
    write_date = NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id
WHERE sc.product_parameter_rel_id = rel.id
  AND rel.active = true
  AND qcp.code = 'MAVI-09'
  AND sc.evaluation_type = 'numeric_range'
  AND sc.min_value = 0
  AND sc.max_value = 0
  AND sc.specification_name ILIKE '%migraci%';

COMMIT;

-- Verificación: no debe quedar ningún MAVI-09 con 0-0
-- SELECT pp.default_code, sc.specification_name, sc.min_value, sc.max_value
-- FROM product_product pp
-- JOIN product_template pt ON pt.id = pp.product_tmpl_id
-- JOIN amunet_quality_parameter_product_rel rel ON rel.product_tmpl_id = pt.id AND rel.active=true
-- JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code='MAVI-09'
-- JOIN amunet_quality_parameter_specification_config sc ON sc.product_parameter_rel_id = rel.id
-- WHERE sc.min_value = 0 AND sc.max_value = 0;
