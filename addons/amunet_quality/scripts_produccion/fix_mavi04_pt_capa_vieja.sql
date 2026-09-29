-- ============================================================
-- SCRIPT: Limpieza MAVI-04 — PT cualitativos y semicuantitativos
-- Desactiva capa vieja (seq=1–6) y duplicados en bloque nuevo
-- Referencia: RAPT-024 (DMCRD01), validado por Diana Flores 2026-09-29
-- Aplica en: amunet_prod
-- ============================================================
-- Qué hace:
--   PASO 1: Desactiva (seq=99) entradas viejas de MAVI-04 con seq=1,2,3,5,6
--           Solo en productos de categoría "Producto terminado / Pruebas rápidas inmunológicas"
--           Nombres afectados: Polvo, Manchas y/o suciedad, Rasgaduras,
--                              Deformidad o deterioro, Sellado
--   PASO 2: Desactiva duplicados en la capa nueva para ese mismo universo:
--           "Rasgaduras" simple en seq=10 (debe ser solo "Polvo" ahí)
--           "Deformidad o deterioro" simple en seq=20 (debe ser "Manchas y/o suciedad")
--           "Rasgaduras" simple en seq=60 (debe ser "Rasgaduras — Prueba")
--           "Deformidad o deterioro" simple en seq=70 (debe ser "Deformidad o deterioro — Prueba")
-- NO toca SPHMC/SPHMT ni MP ni ningún otro tipo de producto.
-- NO borra: desactiva (seq=99). Los análisis existentes no se ven afectados.
-- ============================================================

BEGIN;

-- CTE con los IDs de product_parameter_rel solo de PT inmunológicos (MAVI-04)
WITH pt_rel AS (
  SELECT ppr.id
  FROM amunet_quality_parameter_product_rel ppr
  JOIN product_template pt ON pt.id = ppr.product_tmpl_id
  JOIN product_category pc ON pc.id = pt.categ_id
  JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
  WHERE cp.code = 'MAVI-04'
    AND pc.complete_name = 'Producto terminado / Pruebas rápidas inmunológicas'
)

-- ============================================================
-- PASO 1: Desactivar capa vieja (seq=1, 2, 3, 5, 6)
-- ============================================================
UPDATE amunet_quality_parameter_specification_config
SET sequence = 99, write_date = NOW()
WHERE product_parameter_rel_id IN (SELECT id FROM pt_rel)
  AND sequence IN (1, 2, 3, 5, 6)
  AND specification_name IN (
    'Polvo', 'Manchas y/o suciedad', 'Rasgaduras',
    'Deformidad o deterioro', 'Sellado'
  );
-- Esperado: UPDATE ~425–430 (5 entradas × ~85–90 productos)

-- ============================================================
-- PASO 2: Desactivar duplicados en la capa nueva
-- Solo se desactiva el "plain name" cuando YA EXISTE la versión
-- con sufijo ("— Empaque" / "— Prueba") en el mismo producto
-- ============================================================

-- seq=10: "Rasgaduras" simple (el correcto ahí es "Polvo")
UPDATE amunet_quality_parameter_specification_config
SET sequence = 99, write_date = NOW()
WHERE product_parameter_rel_id IN (SELECT id FROM pt_rel)
  AND sequence = 10
  AND specification_name = 'Rasgaduras';

-- seq=20: "Deformidad o deterioro" simple (el correcto es "Manchas y/o suciedad")
UPDATE amunet_quality_parameter_specification_config
SET sequence = 99, write_date = NOW()
WHERE product_parameter_rel_id IN (SELECT id FROM pt_rel)
  AND sequence = 20
  AND specification_name = 'Deformidad o deterioro';

-- seq=60: "Rasgaduras" simple (el correcto es "Rasgaduras — Prueba")
UPDATE amunet_quality_parameter_specification_config
SET sequence = 99, write_date = NOW()
WHERE product_parameter_rel_id IN (SELECT id FROM pt_rel)
  AND sequence = 60
  AND specification_name = 'Rasgaduras';

-- seq=70: "Deformidad o deterioro" simple (el correcto es "Deformidad o deterioro — Prueba")
UPDATE amunet_quality_parameter_specification_config
SET sequence = 99, write_date = NOW()
WHERE product_parameter_rel_id IN (SELECT id FROM pt_rel)
  AND sequence = 70
  AND specification_name = 'Deformidad o deterioro';

-- ============================================================
-- VERIFICACIÓN FINAL
-- ============================================================

-- Debe devolver 0: no debe quedar ninguna entrada de capa vieja activa
SELECT COUNT(*) as capa_vieja_activa
FROM amunet_quality_parameter_specification_config psc
JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = psc.product_parameter_rel_id
JOIN product_template pt ON pt.id = ppr.product_tmpl_id
JOIN product_category pc ON pc.id = pt.categ_id
JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
WHERE cp.code = 'MAVI-04'
  AND pc.complete_name = 'Producto terminado / Pruebas rápidas inmunológicas'
  AND psc.sequence IN (1, 2, 3, 5, 6);

-- Debe devolver 0: no debe quedar "Sellado" activo
SELECT COUNT(*) as sellado_activo
FROM amunet_quality_parameter_specification_config psc
JOIN amunet_quality_parameter_product_rel ppr ON ppr.id = psc.product_parameter_rel_id
JOIN product_template pt ON pt.id = ppr.product_tmpl_id
JOIN product_category pc ON pc.id = pt.categ_id
JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
WHERE cp.code = 'MAVI-04'
  AND pc.complete_name = 'Producto terminado / Pruebas rápidas inmunológicas'
  AND psc.sequence < 99
  AND psc.specification_name = 'Sellado';

-- Muestra PT que NO quedaron en exactamente 7 MAVI-04 activos
-- Si sale vacío: todo bien
SELECT pt.default_code,
  COUNT(psc.id) FILTER (WHERE psc.sequence < 99) as m04_activas
FROM product_template pt
JOIN amunet_quality_parameter_product_rel ppr ON ppr.product_tmpl_id = pt.id
JOIN product_category pc ON pc.id = pt.categ_id
JOIN amunet_quality_check_parameter cp ON cp.id = ppr.parameter_id
LEFT JOIN amunet_quality_parameter_specification_config psc
  ON psc.product_parameter_rel_id = ppr.id
WHERE cp.code = 'MAVI-04'
  AND pc.complete_name = 'Producto terminado / Pruebas rápidas inmunológicas'
GROUP BY pt.default_code
HAVING COUNT(psc.id) FILTER (WHERE psc.sequence < 99) != 7
ORDER BY pt.default_code;

COMMIT;
