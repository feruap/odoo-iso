-- ============================================================
-- CORRECCIÓN: MAVI-16 faltante en productos Colorimétricos
-- Base de datos: amunet_prod
-- Fecha: 2026-09-21
-- Solicitado por: Diana Flores — Control de Calidad
--
-- Problema: 4 productos clasificados como Colorimétrica no tienen
-- las especificaciones de MAVI-16 (parámetro id=123 "Apariencia
-- colorimétrica") configuradas en Odoo.
--
-- DMALC01  (Alcohol en Saliva)         tmpl_id=1268  → sin rel ni specs
-- DMAMH01  (AMH)                        tmpl_id=1272  → sin rel ni specs
-- DEMAM-001 (Hemoglinet)                tmpl_id=1316  → sin rel ni specs
-- DRAM-001  (Albúmina Semicuantitativa) rel_id=4069   → rel existe, sin specs
--
-- Plantilla de specs tomada de DMIVU01 (rel_id=4686), que ya tiene
-- MAVI-16 correctamente configurado:
--   Spec 1 (spec_id=415): "El color proporcionado corresponde al señalado por el patrón."
--   Spec 2 (spec_id=386): "Visualización de líneas resultado en rango"
--   Tipo: mavi_15_ternary
-- ============================================================

BEGIN;

-- ── 1. DMALC01: crear rel y 2 specs ─────────────────────────────────────────
WITH new_rel AS (
    INSERT INTO amunet_quality_parameter_product_rel
        (product_tmpl_id, parameter_id, active, create_uid, write_uid, create_date, write_date)
    VALUES
        (1268, 123, true, 1, 1, NOW(), NOW())
    RETURNING id
)
INSERT INTO amunet_quality_parameter_specification_config
    (product_parameter_rel_id, specification_id, specification_name,
     evaluation_type, sequence, active, create_uid, write_uid, create_date, write_date)
SELECT nr.id, spec.specification_id, spec.specification_name,
       spec.evaluation_type, spec.sequence, true, 1, 1, NOW(), NOW()
FROM new_rel nr,
     (VALUES
        (415, 'El color proporcionado corresponde al señalado por el patrón.', 'mavi_15_ternary', 10),
        (386, 'Visualización de líneas resultado en rango', 'mavi_15_ternary', 20)
     ) AS spec(specification_id, specification_name, evaluation_type, sequence);

-- ── 2. DMAMH01: crear rel y 2 specs ─────────────────────────────────────────
WITH new_rel AS (
    INSERT INTO amunet_quality_parameter_product_rel
        (product_tmpl_id, parameter_id, active, create_uid, write_uid, create_date, write_date)
    VALUES
        (1272, 123, true, 1, 1, NOW(), NOW())
    RETURNING id
)
INSERT INTO amunet_quality_parameter_specification_config
    (product_parameter_rel_id, specification_id, specification_name,
     evaluation_type, sequence, active, create_uid, write_uid, create_date, write_date)
SELECT nr.id, spec.specification_id, spec.specification_name,
       spec.evaluation_type, spec.sequence, true, 1, 1, NOW(), NOW()
FROM new_rel nr,
     (VALUES
        (415, 'El color proporcionado corresponde al señalado por el patrón.', 'mavi_15_ternary', 10),
        (386, 'Visualización de líneas resultado en rango', 'mavi_15_ternary', 20)
     ) AS spec(specification_id, specification_name, evaluation_type, sequence);

-- ── 3. DEMAM-001: crear rel y 2 specs ───────────────────────────────────────
WITH new_rel AS (
    INSERT INTO amunet_quality_parameter_product_rel
        (product_tmpl_id, parameter_id, active, create_uid, write_uid, create_date, write_date)
    VALUES
        (1316, 123, true, 1, 1, NOW(), NOW())
    RETURNING id
)
INSERT INTO amunet_quality_parameter_specification_config
    (product_parameter_rel_id, specification_id, specification_name,
     evaluation_type, sequence, active, create_uid, write_uid, create_date, write_date)
SELECT nr.id, spec.specification_id, spec.specification_name,
       spec.evaluation_type, spec.sequence, true, 1, 1, NOW(), NOW()
FROM new_rel nr,
     (VALUES
        (415, 'El color proporcionado corresponde al señalado por el patrón.', 'mavi_15_ternary', 10),
        (386, 'Visualización de líneas resultado en rango', 'mavi_15_ternary', 20)
     ) AS spec(specification_id, specification_name, evaluation_type, sequence);

-- ── 4. DRAM-001: solo specs (rel_id=4069 ya existe) ─────────────────────────
INSERT INTO amunet_quality_parameter_specification_config
    (product_parameter_rel_id, specification_id, specification_name,
     evaluation_type, sequence, active, create_uid, write_uid, create_date, write_date)
VALUES
    (4069, 415, 'El color proporcionado corresponde al señalado por el patrón.',
     'mavi_15_ternary', 10, true, 1, 1, NOW(), NOW()),
    (4069, 386, 'Visualización de líneas resultado en rango',
     'mavi_15_ternary', 20, true, 1, 1, NOW(), NOW());

COMMIT;

-- ── Verificación post-ejecución ───────────────────────────────────────────────
-- Debe mostrar 2 specs para cada producto (DMALC01, DMAMH01, DEMAM-001, DRAM-001):
--
-- SELECT pp.default_code, sc.sequence, sc.specification_name
-- FROM product_product pp
-- JOIN product_template pt ON pt.id = pp.product_tmpl_id
-- JOIN amunet_quality_parameter_product_rel rel ON rel.product_tmpl_id = pt.id AND rel.active=true
-- JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code='MAVI-16'
-- JOIN amunet_quality_parameter_specification_config sc ON sc.product_parameter_rel_id = rel.id AND sc.active=true
-- WHERE pp.default_code IN ('DMALC01','DMAMH01','DEMAM-001','DRAM-001')
-- ORDER BY pp.default_code, sc.sequence;
