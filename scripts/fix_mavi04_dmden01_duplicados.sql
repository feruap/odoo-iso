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
-- Resultado esperado para DMDEN01:
--   MAVI-04 empaque (rel_id=4407): 5 specs
--     • Polvo
--     • Manchas y/o suciedad
--     • Rasgaduras
--     • Deformidad o deterioro
--     • Letra adecuada
--   MAVI-04 prueba/tira (rel nuevo): 2 specs
--     • Rasgaduras
--     • Deformidad o deterioro
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

-- ── Paso 4: Agregar segundo MAVI-04 para la tira/prueba ──────────────────────
-- Igual que en DMPSA01/DMTSH02/DMFRT02: rel nuevo + 2 specs (Rasgaduras, Deformidad)
WITH new_rel AS (
    INSERT INTO amunet_quality_parameter_product_rel
        (product_tmpl_id, parameter_id, active, create_uid, write_uid, create_date, write_date)
    VALUES (1298, 145, true, 1, 1, NOW(), NOW())
    RETURNING id
)
INSERT INTO amunet_quality_parameter_specification_config
    (product_parameter_rel_id, specification_id, specification_name,
     evaluation_type, sequence, binary_option_pass, binary_option_fail,
     active, create_uid, write_uid, create_date, write_date)
SELECT nr.id, spec.sid, spec.sname, 'binary_selection', spec.seq,
       spec.pass_opt, spec.fail_opt, true, 1, 1, NOW(), NOW()
FROM new_rel nr,
     (VALUES
        (691, 'Rasgaduras',             10, 'Sin rasgaduras',           'Con rasgaduras'),
        (692, 'Deformidad o deterioro', 20, 'Sin deformidad o deterioro', 'Con deformidad o deterioro')
     ) AS spec(sid, sname, seq, pass_opt, fail_opt);

COMMIT;

-- ── Verificación post-ejecución ───────────────────────────────────────────────
-- Debe mostrar 2 grupos para DMDEN01:
--   Empaque (5 specs): Polvo | Manchas | Rasgaduras | Deformidad | Letra adecuada
--   Prueba  (2 specs): Rasgaduras | Deformidad o deterioro
--
-- SELECT rel.id, rel.active, STRING_AGG(sc.specification_name, ' | ' ORDER BY sc.sequence)
-- FROM product_product pp
-- JOIN product_template pt ON pt.id = pp.product_tmpl_id
-- JOIN amunet_quality_parameter_product_rel rel ON rel.product_tmpl_id = pt.id AND rel.active=true
-- JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code='MAVI-04'
-- LEFT JOIN amunet_quality_parameter_specification_config sc ON sc.product_parameter_rel_id = rel.id AND sc.active=true
-- WHERE pp.default_code = 'DMDEN01'
-- GROUP BY rel.id, rel.active;
