-- ============================================================
-- ACTIVAR qc_required EN PRODUCTOS CON PARÁMETROS CONFIGURADOS
-- Base de datos: amunet_prod
-- Solicitado por: Diana Flores — Control de Calidad
-- Fecha: 2026-09-18
--
-- Activa el flag "Requiere control de calidad" en todos los
-- productos que ya tienen al menos un parámetro activo en el
-- catálogo pero el flag está apagado.
-- Sin este flag, los puntos de control no se muestran al crear
-- un análisis aunque estén configurados.
-- ============================================================

-- Previsualización: qué productos se van a actualizar
SELECT pp.default_code, pt.name->>'es_MX' AS nombre,
       COUNT(r.id) AS params_activos
FROM product_template pt
JOIN product_product pp ON pp.product_tmpl_id = pt.id
JOIN amunet_quality_parameter_product_rel r ON r.product_tmpl_id = pt.id
WHERE pt.active = true AND pp.active = true
  AND pt.qc_required = false
  AND r.active = true
GROUP BY pp.default_code, pt.name->>'es_MX'
ORDER BY pp.default_code;

-- Aplicar cambio
BEGIN;

UPDATE product_template pt
SET qc_required = true,
    write_date  = NOW()
WHERE pt.active = true
  AND pt.qc_required = false
  AND EXISTS (
    SELECT 1
    FROM amunet_quality_parameter_product_rel r
    WHERE r.product_tmpl_id = pt.id
      AND r.active = true
  );

-- Verificar resultado
SELECT COUNT(*) AS productos_actualizados
FROM product_template pt
WHERE qc_required = true
  AND EXISTS (
    SELECT 1 FROM amunet_quality_parameter_product_rel r
    WHERE r.product_tmpl_id = pt.id AND r.active = true
  );

COMMIT;
