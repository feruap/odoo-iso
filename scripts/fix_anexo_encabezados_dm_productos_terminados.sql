-- ============================================================
-- CORRECCIÓN: Encabezados de Anexo para productos DM/DL/DIAM/DRAM/DEMAM
-- Base de datos: amunet_prod
-- Fecha: 2026-09-22
-- Solicitado por: Diana Flores — Control de Calidad
--
-- Problema: Los análisis de producto terminado (DM*, DL*, DIAM*, DRAM*, DEMAM*)
-- creados antes de esta corrección solo tienen col1_header = 'Apariencia'.
-- En el reporte PDF, con t-if, solo aparecen 2 columnas (# Muestra + Apariencia).
-- Los datos de col2-col7 SÍ están guardados en la BD pero sin encabezado no
-- son visibles en el reporte.
--
-- Corrección: Asignar los 7 encabezados estándar del Anexo Producto Terminado
-- a todos los análisis DM/DL/DIAM/DRAM/DEMAM que aún tienen col2_header vacío.
-- Los análisis que ya tienen encabezados personalizados NO se tocan.
--
-- Resultado esperado:
--   tiene_anexos    = true
--   anexo_titulo    = 'ANEXO PRODUCTO TERMINADO'
--   col1_header     = 'Apariencia de Empaque'
--   col2_header     = 'Apariencia de Prueba'
--   col3_header     = 'Hermeticidad'
--   col4_header     = 'Contenido'
--   col5_header     = 'T. Liberación (seg)'
--   col6_header     = 'T. Migración (seg)'
--   col7_header     = 'Desempeño'
-- ============================================================

BEGIN;

UPDATE amunet_quality_check aqc
SET
    tiene_anexos       = true,
    anexo_titulo       = 'ANEXO PRODUCTO TERMINADO',
    anexo_col1_header  = 'Apariencia de Empaque',
    anexo_col2_header  = 'Apariencia de Prueba',
    anexo_col3_header  = 'Hermeticidad',
    anexo_col4_header  = 'Contenido',
    anexo_col5_header  = 'T. Liberación (seg)',
    anexo_col6_header  = 'T. Migración (seg)',
    anexo_col7_header  = 'Desempeño',
    write_date         = NOW()
FROM product_product pp
WHERE aqc.product_id = pp.id
  AND (
      pp.default_code LIKE 'DM%'
   OR pp.default_code LIKE 'DL%'
   OR pp.default_code LIKE 'DIAM%'
   OR pp.default_code LIKE 'DRAM%'
   OR pp.default_code LIKE 'DEMAM%'
  )
  AND (aqc.anexo_col2_header IS NULL OR aqc.anexo_col2_header = '');

-- ── Verificación post-ejecución ───────────────────────────────────────────────
-- Muestra los análisis actualizados y los que ya tenían encabezados:
--
-- SELECT aqc.id, aqc.name, pp.default_code,
--        aqc.tiene_anexos, aqc.anexo_titulo,
--        aqc.anexo_col1_header, aqc.anexo_col2_header,
--        COUNT(al.id) as filas_datos
-- FROM amunet_quality_check aqc
-- JOIN product_product pp ON pp.id = aqc.product_id
-- LEFT JOIN amunet_quality_anexo_line al ON al.check_id = aqc.id
-- WHERE pp.default_code LIKE 'DM%' OR pp.default_code LIKE 'DL%'
-- GROUP BY aqc.id, aqc.name, pp.default_code,
--          aqc.tiene_anexos, aqc.anexo_titulo,
--          aqc.anexo_col1_header, aqc.anexo_col2_header
-- ORDER BY aqc.id DESC LIMIT 20;

COMMIT;
