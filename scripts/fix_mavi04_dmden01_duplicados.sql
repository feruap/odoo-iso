-- ============================================================
-- CORRECCIÓN: MAVI-04 en DMDEN01 (Dengue)
-- Base de datos: amunet_prod
-- Fecha: 2026-09-18
-- Solicitado por: Diana Flores — Control de Calidad
--
-- Problema: DMDEN01 tiene en MAVI-04 (Apariencia física):
--   • "Rasgaduras" duplicada (aparece 2 veces, ids 89496 y 89993)
--   • "Deformidad o deterioro" duplicada (ids 89497 y 89994)
--   • FALTAN: "Polvo" y "Manchas y/o suciedad"
--   → 5 specs incorrectas (3 únicas + 2 duplicados, sin Polvo ni Manchas)
--
-- Corrección:
--   1. Borrar los duplicados (ids 89993 y 89994)
--   2. Insertar las dos specs faltantes: Polvo y Manchas y/o suciedad
--
-- Resultado esperado (5 specs estándar para PT):
--   • Polvo
--   • Manchas y/o suciedad
--   • Rasgaduras
--   • Deformidad o deterioro
--   • Letra adecuada
-- ============================================================

BEGIN;

-- ── Paso 1: Borrar duplicados ────────────────────────────────────────────────
DELETE FROM amunet_quality_parameter_specification_config
WHERE id IN (89993, 89994);

-- ── Paso 2: Agregar "Polvo" (seq 10) ────────────────────────────────────────
INSERT INTO amunet_quality_parameter_specification_config
  (product_parameter_rel_id, specification_id, specification_name,
   evaluation_type, sequence, binary_expected_option,
   binary_option_pass, binary_option_fail,
   product_tmpl_id, parameter_id,
   create_uid, write_uid, create_date, write_date, active)
VALUES
  (4407, 689, 'Polvo',
   'binary_selection', 10, 'with_prefix',
   'Sin polvo', 'Con polvo',
   1298, 145,
   1, 1, NOW(), NOW(), true);

-- ── Paso 3: Agregar "Manchas y/o suciedad" (seq 20) ─────────────────────────
INSERT INTO amunet_quality_parameter_specification_config
  (product_parameter_rel_id, specification_id, specification_name,
   evaluation_type, sequence, binary_expected_option,
   binary_option_pass, binary_option_fail,
   product_tmpl_id, parameter_id,
   create_uid, write_uid, create_date, write_date, active)
VALUES
  (4407, 690, 'Manchas y/o suciedad',
   'binary_selection', 20, 'with_prefix',
   'Sin manchas y/o suciedad', 'Con manchas y/o suciedad',
   1298, 145,
   1, 1, NOW(), NOW(), true);

COMMIT;

-- ── Verificación post-ejecución ───────────────────────────────────────────────
-- Debe mostrar exactamente 5 filas para DMDEN01:
--   Polvo | Manchas y/o suciedad | Rasgaduras | Deformidad o deterioro | Letra adecuada
--
-- SELECT sc.id, sc.sequence, sc.specification_name, sc.binary_option_pass, sc.binary_option_fail
-- FROM product_product pp
-- JOIN product_template pt ON pt.id = pp.product_tmpl_id
-- JOIN amunet_quality_parameter_product_rel rel ON rel.product_tmpl_id = pt.id AND rel.active=true
-- JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code='MAVI-04'
-- JOIN amunet_quality_parameter_specification_config sc ON sc.product_parameter_rel_id = rel.id
-- WHERE pp.default_code = 'DMDEN01'
-- ORDER BY sc.sequence;
