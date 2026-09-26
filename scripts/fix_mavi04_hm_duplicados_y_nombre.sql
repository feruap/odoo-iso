-- ============================================================
-- CORRECCIÓN: MAVI-04 en Hojas Maestras SPHMC/SPHMT
-- Base de datos: amunet_prod
-- Fecha: 2026-09-18
-- Solicitado por: Diana Flores — Control de Calidad
--
-- Problema: TODAS las hojas maestras de antidoping (SPHMC01-88
-- y SPHMT01-12) tienen en MAVI-04 (Apariencia física):
--   • "Deformidad o deterioro." duplicada (aparece 2 veces, con punto)
--   • "Adecuado" con nombre incorrecto (debe ser "Letra adecuada")
--   → 5 specs incorrectas donde deben ser 4 correctas
--
-- Corrección aplicada:
--   1. Eliminar el duplicado (queda solo UNA "Deformidad o deterioro")
--   2. Quitar el punto al final de "Deformidad o deterioro."
--   3. Renombrar "Adecuado" → "Letra adecuada"
--
-- Resultado esperado (4 specs por cada HM):
--   • Manchas y/o suciedad
--   • Rasgaduras
--   • Deformidad o deterioro
--   • Letra adecuada
-- ============================================================

BEGIN;

-- ── Paso 1: Borrar el spec duplicado de "Deformidad o deterioro." ─────────────
-- Se conserva el de ID más alto (el más reciente); se borra el sobrante.
DELETE FROM amunet_quality_parameter_specification_config sc
WHERE sc.specification_name = 'Deformidad o deterioro.'
  AND sc.id NOT IN (
      SELECT MAX(sc2.id)
      FROM amunet_quality_parameter_specification_config sc2
      WHERE sc2.specification_name = 'Deformidad o deterioro.'
      GROUP BY sc2.product_parameter_rel_id
  )
  AND sc.product_parameter_rel_id IN (
      SELECT rel.id
      FROM amunet_quality_parameter_product_rel rel
      JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id
      JOIN product_template pt ON pt.id = rel.product_tmpl_id
      JOIN product_product pp ON pp.product_tmpl_id = pt.id
      WHERE rel.active = true
        AND qcp.code = 'MAVI-04'
        AND (pp.default_code LIKE 'SPHMC%' OR pp.default_code LIKE 'SPHMT%')
  );

-- ── Paso 2: Quitar el punto de "Deformidad o deterioro." ─────────────────────
UPDATE amunet_quality_parameter_specification_config sc
SET specification_name = 'Deformidad o deterioro',
    write_date = NOW()
WHERE sc.specification_name = 'Deformidad o deterioro.'
  AND sc.product_parameter_rel_id IN (
      SELECT rel.id
      FROM amunet_quality_parameter_product_rel rel
      JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id
      JOIN product_template pt ON pt.id = rel.product_tmpl_id
      JOIN product_product pp ON pp.product_tmpl_id = pt.id
      WHERE rel.active = true
        AND qcp.code = 'MAVI-04'
        AND (pp.default_code LIKE 'SPHMC%' OR pp.default_code LIKE 'SPHMT%')
  );

-- ── Paso 3: Renombrar "Adecuado" → "Letra adecuada" ─────────────────────────
UPDATE amunet_quality_parameter_specification_config sc
SET specification_name = 'Letra adecuada',
    write_date = NOW()
WHERE sc.specification_name = 'Adecuado'
  AND sc.product_parameter_rel_id IN (
      SELECT rel.id
      FROM amunet_quality_parameter_product_rel rel
      JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id
      JOIN product_template pt ON pt.id = rel.product_tmpl_id
      JOIN product_product pp ON pp.product_tmpl_id = pt.id
      WHERE rel.active = true
        AND qcp.code = 'MAVI-04'
        AND (pp.default_code LIKE 'SPHMC%' OR pp.default_code LIKE 'SPHMT%')
  );

COMMIT;

-- ── Verificación post-ejecución ───────────────────────────────────────────────
-- Debe mostrar exactamente 4 filas por cada SPHMC/SPHMT:
--   Manchas y/o suciedad | Rasgaduras | Deformidad o deterioro | Letra adecuada
--
-- SELECT pp.default_code, sc.specification_name
-- FROM product_product pp
-- JOIN product_template pt ON pt.id = pp.product_tmpl_id
-- JOIN amunet_quality_parameter_product_rel rel ON rel.product_tmpl_id = pt.id AND rel.active=true
-- JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code='MAVI-04'
-- JOIN amunet_quality_parameter_specification_config sc ON sc.product_parameter_rel_id = rel.id
-- WHERE pp.default_code LIKE 'SPHMC%' OR pp.default_code LIKE 'SPHMT%'
-- ORDER BY pp.default_code, sc.id;
