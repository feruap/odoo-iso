-- ============================================================
-- SCRIPT: Limpieza de duplicados MAVI-15 en PTs semicuantitativos
-- (DMFRT02 Ferrinet, DMPSA01 PSA semicuantitativa, DMTSH02 TSH)
-- Preparado: 2026-09-28
-- Ejecutar en amunet_prod, por Fernando/desarrollo
-- Validado en staging: 3 x DELETE 2 = 6 registros eliminados
-- ============================================================
-- Resultado esperado después: cada PT tiene solo 2 entradas MAVI-15
--   Control negativo (seq 10) + Control positivo (seq 20)
-- ============================================================

BEGIN;

-- DMFRT02: conservar 89224 (neg, seq 10) y 89225 (pos, seq 20)
-- borrar 89071 (neg, seq 10) y 89072 (pos, seq 10) — 0 referencias
DELETE FROM amunet_quality_parameter_specification_config
WHERE id IN (89071, 89072);

-- DMPSA01: conservar 89237 (neg) y 89238 (pos) — usados en análisis 895 (done)
-- borrar 89075 (neg, seq 10) y 89076 (pos, seq 10) — 0 referencias
DELETE FROM amunet_quality_parameter_specification_config
WHERE id IN (89075, 89076);

-- DMTSH02: conservar 89211 (neg, seq 10) y 89212 (pos, seq 20)
-- borrar 89073 (neg, seq 10) y 89074 (pos, seq 10) — 0 referencias
DELETE FROM amunet_quality_parameter_specification_config
WHERE id IN (89073, 89074);

-- Verificación — debe mostrar 2 filas por producto
SELECT pt.default_code, psc.id, psc.specification_name, psc.sequence
FROM product_template pt
JOIN amunet_quality_parameter_product_rel ppr ON ppr.product_tmpl_id = pt.id
JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
JOIN amunet_quality_parameter_specification_config psc ON psc.product_parameter_rel_id = ppr.id
WHERE pt.default_code IN ('DMFRT02','DMPSA01','DMTSH02') AND cp.code = 'MAVI-15'
ORDER BY pt.default_code, psc.sequence;

COMMIT;
