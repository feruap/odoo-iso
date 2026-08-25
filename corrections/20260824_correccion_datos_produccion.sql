-- ============================================================
-- CORRECCIÓN DE DATOS EN PRODUCCIÓN (amunet_prod)
-- Solicitado por: Diana Flores (s.controldecalidad@amunet.com.mx)
-- Fecha: 2026-08-24
-- Motivo: Resultados MAVI-11 no capturados en análisis cerrados;
--         descripciones de producto incorrectas.
-- Autorizado para aplicar por: Mery (desarrollo)
-- ============================================================

BEGIN;

-- ============================================================
-- 1. MAVI-11 — Cartucho Tuberculosis
--    Análisis: QC/2026/00007 | Lote: CAR28072601
-- ============================================================
UPDATE amunet_quality_test_line_detail SET
    result_numeric = 0.1, result_numeric_filled = true
WHERE id = 4611; -- Cierre completo (máx 0.50)

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 3.7, result_numeric_filled = true
WHERE id = 4613; -- Interna (Ventana) Ancho (máx 4.50)

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 15.2, result_numeric_filled = true
WHERE id = 4612; -- Interna (Ventana) Largo (máx 18.00)

-- ============================================================
-- 2. MAVI-11 — Cartucho Calprotectina
--    Análisis: QC/2026/00032 | Lote: CAR55072601
-- ============================================================
UPDATE amunet_quality_test_line_detail SET
    result_numeric = 0.1, result_numeric_filled = true
WHERE id = 4820; -- Cierre completo

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 3.2, result_numeric_filled = true
WHERE id = 4822; -- Interna (Ventana) Ancho

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 14.5, result_numeric_filled = true
WHERE id = 4821; -- Interna (Ventana) Largo

-- ============================================================
-- 3. MAVI-11 — Cartucho Entamoeba
--    Análisis: QC/2026/00033 | Lote: CAR48072601
-- ============================================================
UPDATE amunet_quality_test_line_detail SET
    result_numeric = 0.1, result_numeric_filled = true
WHERE id = 4831; -- Cierre completo

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 2.8, result_numeric_filled = true
WHERE id = 4833; -- Interna (Ventana) Ancho

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 14.5, result_numeric_filled = true
WHERE id = 4832; -- Interna (Ventana) Largo

-- ============================================================
-- 4. MAVI-11 — Cartucho Factor Reumatoide
--    Análisis: QC/2026/00035 | Lote: CAR42072601
-- ============================================================
UPDATE amunet_quality_test_line_detail SET
    result_numeric = 0.1, result_numeric_filled = true
WHERE id = 4853; -- Cierre completo

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 2.3, result_numeric_filled = true
WHERE id = 4855; -- Interna (Ventana) Ancho

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 14.0, result_numeric_filled = true
WHERE id = 4854; -- Interna (Ventana) Largo

-- ============================================================
-- 5. MAVI-11 — Cartucho Chagas
--    Análisis: QC/2026/00034 | Lote: CAR05072601
-- ============================================================
UPDATE amunet_quality_test_line_detail SET
    result_numeric = 0.1, result_numeric_filled = true
WHERE id = 4842; -- Cierre completo

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 2.5, result_numeric_filled = true
WHERE id = 4844; -- Interna (Ventana) Ancho

UPDATE amunet_quality_test_line_detail SET
    result_numeric = 14.0, result_numeric_filled = true
WHERE id = 4843; -- Interna (Ventana) Largo

-- ============================================================
-- 6. Agentes biológicos — Agua Bidestilada
--    Análisis: QC/2026/00017 | Lote: ABI01082601
--    Valor: < 1 UFC (se registra como 0 en campo numérico)
-- ============================================================
UPDATE amunet_quality_test_line_detail SET
    result_numeric = 0, result_numeric_filled = true
WHERE id = 5933; -- Agentes biológicos (criterio: ≤100 UFC/10 mL)

-- ============================================================
-- 7. Descripción — MPCAR53 Cartucho Antidoping 5P saliva
--    Cambio permanente a nivel producto
-- ============================================================
UPDATE product_template SET
    description = '{"en_US": "<p>Cartucho para prueba rápida de antidoping 5 parámetros en muestras de saliva</p>", "es_MX": "<p>Cartucho para prueba rápida de antidoping 5 parámetros en muestras de saliva</p>"}'::jsonb
WHERE default_code = 'MPCAR53';

-- ============================================================
-- 8. Descripción — SPHMC53 Hoja Maestra Antidoping 2P saliva
-- ============================================================
UPDATE product_template SET
    description = '{"en_US": "<p>Hoja maestra para la detección de Antidoping 2 parámetros (MET y THC) en muestras de saliva</p>", "es_MX": "<p>Hoja maestra para la detección de Antidoping 2 parámetros (MET y THC) en muestras de saliva</p>"}'::jsonb
WHERE default_code = 'SPHMC53';

-- ============================================================
-- 9. Descripción — SPHMC54 Hoja Maestra Antidoping 3P saliva
-- ============================================================
UPDATE product_template SET
    description = '{"en_US": "<p>Hoja maestra para la detección de Antidoping 3 parámetros (OPI, COC y AMP) en muestras de saliva</p>", "es_MX": "<p>Hoja maestra para la detección de Antidoping 3 parámetros (OPI, COC y AMP) en muestras de saliva</p>"}'::jsonb
WHERE default_code = 'SPHMC54';

-- ============================================================
-- 10. Descripciones — Buffers de proveedor STBPR01-04 + STREX01-02
-- ============================================================
UPDATE product_template SET description='{"es_MX": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras de sangre, suero o plasma</p>", "en_US": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras de sangre, suero o plasma</p>"}'::jsonb WHERE default_code='STBPR01';
UPDATE product_template SET description='{"es_MX": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras orofaríngeas, nasofaríngeas o salivales</p>", "en_US": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras orofaríngeas, nasofaríngeas o salivales</p>"}'::jsonb WHERE default_code='STBPR02';
UPDATE product_template SET description='{"es_MX": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras de heces</p>", "en_US": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras de heces</p>"}'::jsonb WHERE default_code='STBPR03';
UPDATE product_template SET description='{"es_MX": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras HV</p>", "en_US": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas con muestras HV</p>"}'::jsonb WHERE default_code='STBPR04';
UPDATE product_template SET description='{"es_MX": "<p>Vial con reactivo de extracción 1 para pruebas rápidas</p>", "en_US": "<p>Vial con reactivo de extracción 1 para pruebas rápidas</p>"}'::jsonb WHERE default_code='STREX01';
UPDATE product_template SET description='{"es_MX": "<p>Vial con reactivo de extracción 2 para pruebas rápidas</p>", "en_US": "<p>Vial con reactivo de extracción 2 para pruebas rápidas</p>"}'::jsonb WHERE default_code='STREX02';

-- ============================================================
-- 11. Descripción — STBPC01 (clave conjunta buffers de proveedor)
--     NOTA: STBPC01 solo existe en producción, no en staging.
-- ============================================================
UPDATE product_template SET description='{"es_MX": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas</p>", "en_US": "<p>Vial con solución de corrimiento de proveedor para pruebas rápidas</p>"}'::jsonb WHERE default_code='STBPC01';

COMMIT;

-- Verificación rápida post-aplicación:
SELECT 'TB Cierre' as campo, result_numeric FROM amunet_quality_test_line_detail WHERE id=4611
UNION ALL SELECT 'TB Ancho', result_numeric FROM amunet_quality_test_line_detail WHERE id=4613
UNION ALL SELECT 'TB Largo', result_numeric FROM amunet_quality_test_line_detail WHERE id=4612
UNION ALL SELECT 'Calp Cierre', result_numeric FROM amunet_quality_test_line_detail WHERE id=4820
UNION ALL SELECT 'Calp Ancho', result_numeric FROM amunet_quality_test_line_detail WHERE id=4822
UNION ALL SELECT 'Calp Largo', result_numeric FROM amunet_quality_test_line_detail WHERE id=4821
UNION ALL SELECT 'Enta Cierre', result_numeric FROM amunet_quality_test_line_detail WHERE id=4831
UNION ALL SELECT 'Enta Ancho', result_numeric FROM amunet_quality_test_line_detail WHERE id=4833
UNION ALL SELECT 'Enta Largo', result_numeric FROM amunet_quality_test_line_detail WHERE id=4832
UNION ALL SELECT 'FR Cierre', result_numeric FROM amunet_quality_test_line_detail WHERE id=4853
UNION ALL SELECT 'FR Ancho', result_numeric FROM amunet_quality_test_line_detail WHERE id=4855
UNION ALL SELECT 'FR Largo', result_numeric FROM amunet_quality_test_line_detail WHERE id=4854
UNION ALL SELECT 'Chagas Cierre', result_numeric FROM amunet_quality_test_line_detail WHERE id=4842
UNION ALL SELECT 'Chagas Ancho', result_numeric FROM amunet_quality_test_line_detail WHERE id=4844
UNION ALL SELECT 'Chagas Largo', result_numeric FROM amunet_quality_test_line_detail WHERE id=4843
UNION ALL SELECT 'ABI Agentes bio', result_numeric FROM amunet_quality_test_line_detail WHERE id=5933;
