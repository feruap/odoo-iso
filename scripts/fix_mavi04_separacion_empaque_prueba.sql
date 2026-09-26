-- ============================================================
-- CORRECCIÓN: Separar MAVI-04 en empaque vs prueba — DMESC01
-- Base de datos: amunet_prod
-- Fecha: 2026-09-17
-- Solicitado por: Diana Flores — Control de Calidad
--
-- El MAVI-04 de DMESC01 tiene 7 aspectos sin etiqueta de sección.
-- Se renombran los items para que quede claro cuáles son de
-- empaque y cuáles de la prueba.
--
-- Afecta DOS lugares:
--   1. El CATÁLOGO (amunet_quality_parameter_specification_config)
--      para que los nuevos análisis nazcan con los nombres correctos.
--   2. El ANÁLISIS 902 (QC/2026/00473) que ya está en progreso,
--      para corregir sus detalles actuales.
-- ============================================================

BEGIN;

-- ── 1. CATÁLOGO: spec_configs del rel_id 4432 (MAVI-04 activo de DMESC01) ──

-- Items de EMPAQUE (89549–89553): agregar "— Empaque"
UPDATE amunet_quality_parameter_specification_config
SET specification_name = 'Polvo — Empaque', write_date = NOW()
WHERE id = 89549;

UPDATE amunet_quality_parameter_specification_config
SET specification_name = 'Manchas y/o suciedad — Empaque', write_date = NOW()
WHERE id = 89550;

UPDATE amunet_quality_parameter_specification_config
SET specification_name = 'Rasgaduras — Empaque', write_date = NOW()
WHERE id = 89551;

UPDATE amunet_quality_parameter_specification_config
SET specification_name = 'Deformidad o deterioro — Empaque', write_date = NOW()
WHERE id = 89552;

UPDATE amunet_quality_parameter_specification_config
SET specification_name = 'Letra adecuada — Empaque', write_date = NOW()
WHERE id = 89553;

-- Items de PRUEBA (90003–90004): agregar "— Prueba"
UPDATE amunet_quality_parameter_specification_config
SET specification_name = 'Rasgaduras — Prueba', write_date = NOW()
WHERE id = 90003;

UPDATE amunet_quality_parameter_specification_config
SET specification_name = 'Deformidad o deterioro — Prueba', write_date = NOW()
WHERE id = 90004;

-- ── 2. ANÁLISIS 902 (QC/2026/00473): corregir detalles ya cargados ──

UPDATE amunet_quality_test_line_detail SET name = 'Polvo — Empaque', write_date = NOW()               WHERE id = 9277;
UPDATE amunet_quality_test_line_detail SET name = 'Manchas y/o suciedad — Empaque', write_date = NOW() WHERE id = 9278;
UPDATE amunet_quality_test_line_detail SET name = 'Rasgaduras — Empaque', write_date = NOW()           WHERE id = 9279;
UPDATE amunet_quality_test_line_detail SET name = 'Deformidad o deterioro — Empaque', write_date = NOW() WHERE id = 9280;
UPDATE amunet_quality_test_line_detail SET name = 'Letra adecuada — Empaque', write_date = NOW()       WHERE id = 9281;
UPDATE amunet_quality_test_line_detail SET name = 'Rasgaduras — Prueba', write_date = NOW()            WHERE id = 9282;
UPDATE amunet_quality_test_line_detail SET name = 'Deformidad o deterioro — Prueba', write_date = NOW() WHERE id = 9283;

COMMIT;

-- Verificación:
-- SELECT tld.id, tld.name
-- FROM amunet_quality_test_line tl
-- JOIN amunet_quality_check_parameter qcp ON qcp.id = tl.parameter_id
-- JOIN amunet_quality_test_line_detail tld ON tld.test_line_id = tl.id
-- WHERE tl.check_id = 902 AND qcp.code = 'MAVI-04'
-- ORDER BY tld.id;
