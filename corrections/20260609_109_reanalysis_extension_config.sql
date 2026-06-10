-- Configuración de meses de extensión de caducidad por reanálisis
-- Según tabla aprobada por Diana Flores (Calidad) - 09/jun/2026

-- ====================================================
-- Por categoría
-- ====================================================

-- Cartucho (Materia prima): 12 meses
UPDATE product_category SET reanalysis_extension_months = 12 WHERE id = 14;

-- Membrana: 12 meses
UPDATE product_category SET reanalysis_extension_months = 12 WHERE id = 37;

-- Almohadilla (sin pretratar): 12 meses
UPDATE product_category SET reanalysis_extension_months = 12 WHERE id = 23;

-- Almohadilla pretratada: 3 meses
UPDATE product_category SET reanalysis_extension_months = 3 WHERE id = 42;

-- Buffer: 3 meses
UPDATE product_category SET reanalysis_extension_months = 3 WHERE id = 34;

-- Envase (Materia prima): 12 meses
UPDATE product_category SET reanalysis_extension_months = 12 WHERE id = 11;

-- Gotero: 12 meses
UPDATE product_category SET reanalysis_extension_months = 12 WHERE id = 35;

-- Hoja maestra (default sangre): 3 meses
UPDATE product_category SET reanalysis_extension_months = 3 WHERE id = 27;

-- Soluciones: 0 (no aplica)
UPDATE product_category SET reanalysis_extension_months = 0 WHERE id IN (16, 51);

-- Cajas (Material impreso): 0 (sin caducidad)
UPDATE product_category SET reanalysis_extension_months = 0 WHERE id = 20;

-- Lanceta: 0 (no aplica por esterilidad)
UPDATE product_category SET reanalysis_extension_months = 0 WHERE id = 30;

-- Hisopo: 0 (no aplica por esterilidad)
UPDATE product_category SET reanalysis_extension_months = 0 WHERE id = 36;

-- ====================================================
-- Overrides por producto (Hoja maestra con muestra diferente)
-- ====================================================

-- Hoja maestra orina: 6 meses
-- SPHMT06 (hCG orina), SPHMT02 (Infecciones urinarias)
UPDATE product_template SET reanalysis_extension_months = 6
WHERE default_code IN ('SPHMT06', 'SPHMT02');

-- Hoja maestra pH vaginal / alcohol saliva: 12 meses
-- SPHMC67 (Alcohol en saliva), SPHMC68 (pH vaginal)
UPDATE product_template SET reanalysis_extension_months = 12
WHERE default_code IN ('SPHMC67', 'SPHMC68');

-- Verificación
SELECT 'Categorías' as tipo, name, reanalysis_extension_months
FROM product_category
WHERE reanalysis_extension_months > 0
ORDER BY reanalysis_extension_months DESC, name;
