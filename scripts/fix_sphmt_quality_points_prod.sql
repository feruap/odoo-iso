-- ============================================================
-- Fix: Asignar puntos de control a hojas maestras SPHMT
-- Aplicar en: amunet_prod
-- Fecha: 2026-09-28
-- Aprobado por: Diana Flores (Calidad)
-- ============================================================

BEGIN;

-- 1. SPHMT03-05: los nuevos activos (creados sep-2026) no tienen punto asignado.
--    Los viejos archivados sí lo tienen. Migramos la asignación.

-- Variant IDs nuevos activos: SPHMT03=2201, SPHMT04=2202, SPHMT05=2203
-- Quality point IDs: SPHMT03->308, SPHMT04->309, SPHMT05->310

INSERT INTO amunet_quality_point_product_product_rel
  (amunet_quality_point_id, product_product_id)
VALUES
  (308, 2201),  -- SPHMT03 nuevo activo -> Hoja Maestra VPH
  (309, 2202),  -- SPHMT04 nuevo activo -> Hoja Maestra Pylorinet
  (310, 2203)   -- SPHMT05 nuevo activo -> Hoja Maestra TB-DxNet
ON CONFLICT DO NOTHING;

-- 2. SPHMT07-12: productos activos sin ningún punto de control asignado.
--    Se enlazan a los mismos puntos que sus equivalentes SPHMC.

-- Variant IDs en producción: SPHMT07-12 (obtener con la query de abajo)
-- SELECT pp.id, pt.default_code FROM product_template pt
-- JOIN product_product pp ON pp.product_tmpl_id = pt.id
-- WHERE pt.default_code IN ('SPHMT07','SPHMT08','SPHMT09','SPHMT10','SPHMT11','SPHMT12')
--   AND pt.active = true;

-- *** NOTA: Obtener los variant_ids de producción antes de ejecutar ***
-- Los IDs siguientes son PLACEHOLDERS — reemplazar con los reales de producción:

-- INSERT INTO amunet_quality_point_product_product_rel
--   (amunet_quality_point_id, product_product_id)
-- VALUES
--   (160, <variant_id_SPHMT07>),  -- Hoja Maestra Marihuana (THC)
--   (320, <variant_id_SPHMT08>),  -- Hoja Maestra Anfetamina (AMP)
--   (121, <variant_id_SPHMT09>),  -- Hoja Maestra Cocaina (COC)
--   (247, <variant_id_SPHMT10>),  -- Hoja Maestra Metanfetamina (MET)
--   (248, <variant_id_SPHMT11>),  -- Hoja Maestra Opiáceos (OPI)
--   (294, <variant_id_SPHMT12>)   -- Hoja Maestra Fentanilo
-- ON CONFLICT DO NOTHING;

COMMIT;
