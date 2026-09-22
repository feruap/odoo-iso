-- ================================================================
-- CORRECCIÓN DE RAÍZ: MAVI-04 en todos los productos DM/DL/DIAM/DRAM/DEMAM
-- Base: Amunet_testing
-- Problema 1: seq 60/70 tienen nombre igual que empaque (sin sufijo — Prueba)
-- Problema 2: seq 30/40 no tienen sufijo — Empaque (ambigüedad)
-- Problema 3: 34 productos DM solo tienen empaque (faltan seq 60/70)
-- Problema 4: 3 productos con 2 rels (DMPSA01/DMTSH02/DMFRT02): rel-prueba sin sufijo
-- ================================================================

BEGIN;

-- ── PASO 1: Renombrar seq 30 "Rasgaduras" → "Rasgaduras — Empaque"
--    (aplica a todos los DM/DL/DIAM/DRAM/DEMAM con ese nombre sin sufijo)
UPDATE amunet_quality_parameter_specification_config sc
SET specification_name = 'Rasgaduras — Empaque',
    write_date = NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code = 'MAVI-04'
JOIN product_product pp ON pp.product_tmpl_id = rel.product_tmpl_id
WHERE sc.product_parameter_rel_id = rel.id
  AND rel.active = true
  AND sc.active = true
  AND sc.sequence = 30
  AND sc.specification_name = 'Rasgaduras'
  AND (pp.default_code LIKE 'DM%' OR pp.default_code LIKE 'DL%'
       OR pp.default_code LIKE 'DIAM%' OR pp.default_code LIKE 'DRAM%'
       OR pp.default_code LIKE 'DEMAM%');

-- ── PASO 2: Renombrar seq 40 "Deformidad o deterioro" → "Deformidad o deterioro — Empaque"
UPDATE amunet_quality_parameter_specification_config sc
SET specification_name = 'Deformidad o deterioro — Empaque',
    write_date = NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code = 'MAVI-04'
JOIN product_product pp ON pp.product_tmpl_id = rel.product_tmpl_id
WHERE sc.product_parameter_rel_id = rel.id
  AND rel.active = true
  AND sc.active = true
  AND sc.sequence = 40
  AND sc.specification_name = 'Deformidad o deterioro'
  AND (pp.default_code LIKE 'DM%' OR pp.default_code LIKE 'DL%'
       OR pp.default_code LIKE 'DIAM%' OR pp.default_code LIKE 'DRAM%'
       OR pp.default_code LIKE 'DEMAM%');

-- ── PASO 3: Renombrar seq 60 "Rasgaduras" → "Rasgaduras — Prueba"
--    (los 43 productos con duplicado en seq 60)
UPDATE amunet_quality_parameter_specification_config sc
SET specification_name = 'Rasgaduras — Prueba',
    write_date = NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code = 'MAVI-04'
JOIN product_product pp ON pp.product_tmpl_id = rel.product_tmpl_id
WHERE sc.product_parameter_rel_id = rel.id
  AND rel.active = true
  AND sc.active = true
  AND sc.sequence = 60
  AND sc.specification_name = 'Rasgaduras'
  AND (pp.default_code LIKE 'DM%' OR pp.default_code LIKE 'DL%'
       OR pp.default_code LIKE 'DIAM%' OR pp.default_code LIKE 'DRAM%'
       OR pp.default_code LIKE 'DEMAM%');

-- ── PASO 4: Renombrar seq 70 "Deformidad o deterioro" → "Deformidad o deterioro — Prueba"
UPDATE amunet_quality_parameter_specification_config sc
SET specification_name = 'Deformidad o deterioro — Prueba',
    write_date = NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code = 'MAVI-04'
JOIN product_product pp ON pp.product_tmpl_id = rel.product_tmpl_id
WHERE sc.product_parameter_rel_id = rel.id
  AND rel.active = true
  AND sc.active = true
  AND sc.sequence = 70
  AND sc.specification_name = 'Deformidad o deterioro'
  AND (pp.default_code LIKE 'DM%' OR pp.default_code LIKE 'DL%'
       OR pp.default_code LIKE 'DIAM%' OR pp.default_code LIKE 'DRAM%'
       OR pp.default_code LIKE 'DEMAM%');

-- ── PASO 5: Para las 3 rels-prueba con 2 rels (DMPSA01/DMTSH02/DMFRT02)
--    renombrar seq 10/20 de la rel-prueba a "— Prueba"
--    (identificadas: seq=10 con "Rasgaduras" en rels que NO tienen seq=50)
UPDATE amunet_quality_parameter_specification_config sc
SET specification_name = 'Rasgaduras — Prueba',
    write_date = NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code = 'MAVI-04'
JOIN product_product pp ON pp.product_tmpl_id = rel.product_tmpl_id
WHERE sc.product_parameter_rel_id = rel.id
  AND rel.active = true
  AND sc.active = true
  AND sc.sequence = 10
  AND sc.specification_name = 'Rasgaduras'
  AND pp.default_code IN ('DMPSA01','DMTSH02','DMFRT02')
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config sc3
    WHERE sc3.product_parameter_rel_id = rel.id AND sc3.active = true AND sc3.sequence = 50
  );

UPDATE amunet_quality_parameter_specification_config sc
SET specification_name = 'Deformidad o deterioro — Prueba',
    write_date = NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code = 'MAVI-04'
JOIN product_product pp ON pp.product_tmpl_id = rel.product_tmpl_id
WHERE sc.product_parameter_rel_id = rel.id
  AND rel.active = true
  AND sc.active = true
  AND sc.sequence = 20
  AND sc.specification_name = 'Deformidad o deterioro'
  AND pp.default_code IN ('DMPSA01','DMTSH02','DMFRT02')
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config sc3
    WHERE sc3.product_parameter_rel_id = rel.id AND sc3.active = true AND sc3.sequence = 50
  );

-- ── PASO 6: Insertar "Rasgaduras — Prueba" (seq 60) para los 34 DM/DL/DIAM
--    productos con solo 5 specs (sin seq >= 60), excluyendo los de 2 rels ya corregidos
INSERT INTO amunet_quality_parameter_specification_config
  (product_parameter_rel_id, specification_id, specification_name,
   evaluation_type, sequence, binary_option_pass, binary_option_fail,
   active, create_uid, write_uid, create_date, write_date)
SELECT rel.id, 691, 'Rasgaduras — Prueba', 'binary_selection', 60,
       'Sin rasgaduras', 'Con rasgaduras', true, 1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code = 'MAVI-04'
JOIN product_product pp ON pp.product_tmpl_id = rel.product_tmpl_id
WHERE rel.active = true
  AND (pp.default_code LIKE 'DM%' OR pp.default_code LIKE 'DL%'
       OR pp.default_code LIKE 'DIAM%' OR pp.default_code LIKE 'DRAM%'
       OR pp.default_code LIKE 'DEMAM%')
  AND pp.default_code NOT IN ('DMPSA01','DMTSH02','DMFRT02')
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config sc2
    WHERE sc2.product_parameter_rel_id = rel.id AND sc2.active = true AND sc2.sequence >= 60
  );

-- ── PASO 7: Insertar "Deformidad o deterioro — Prueba" (seq 70)
INSERT INTO amunet_quality_parameter_specification_config
  (product_parameter_rel_id, specification_id, specification_name,
   evaluation_type, sequence, binary_option_pass, binary_option_fail,
   active, create_uid, write_uid, create_date, write_date)
SELECT rel.id, 692, 'Deformidad o deterioro — Prueba', 'binary_selection', 70,
       'Sin deformidad o deterioro', 'Con deformidad o deterioro',
       true, 1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code = 'MAVI-04'
JOIN product_product pp ON pp.product_tmpl_id = rel.product_tmpl_id
WHERE rel.active = true
  AND (pp.default_code LIKE 'DM%' OR pp.default_code LIKE 'DL%'
       OR pp.default_code LIKE 'DIAM%' OR pp.default_code LIKE 'DRAM%'
       OR pp.default_code LIKE 'DEMAM%')
  AND pp.default_code NOT IN ('DMPSA01','DMTSH02','DMFRT02')
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config sc2
    WHERE sc2.product_parameter_rel_id = rel.id AND sc2.active = true AND sc2.sequence >= 60
  );

COMMIT;

-- ── COMPLEMENTO: specs restantes con secuencias no estándar (3/5/10) ──────────
-- Ejecutar DESPUÉS del script principal si aún quedan sin sufijo
UPDATE amunet_quality_parameter_specification_config sc
SET specification_name = 'Rasgaduras — Empaque', write_date = NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code = 'MAVI-04'
JOIN product_product pp ON pp.product_tmpl_id = rel.product_tmpl_id
WHERE sc.product_parameter_rel_id = rel.id
  AND rel.active = true AND sc.active = true
  AND sc.specification_name = 'Rasgaduras'
  AND (pp.default_code LIKE 'DM%' OR pp.default_code LIKE 'DL%'
       OR pp.default_code LIKE 'DIAM%' OR pp.default_code LIKE 'DRAM%'
       OR pp.default_code LIKE 'DEMAM%');

UPDATE amunet_quality_parameter_specification_config sc
SET specification_name = 'Deformidad o deterioro — Empaque', write_date = NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code = 'MAVI-04'
JOIN product_product pp ON pp.product_tmpl_id = rel.product_tmpl_id
WHERE sc.product_parameter_rel_id = rel.id
  AND rel.active = true AND sc.active = true
  AND sc.specification_name = 'Deformidad o deterioro'
  AND (pp.default_code LIKE 'DM%' OR pp.default_code LIKE 'DL%'
       OR pp.default_code LIKE 'DIAM%' OR pp.default_code LIKE 'DRAM%'
       OR pp.default_code LIKE 'DEMAM%');

-- INSERT Deformidad — Prueba para los 48 DM productos que no tenían
INSERT INTO amunet_quality_parameter_specification_config
  (product_parameter_rel_id, specification_id, specification_name,
   evaluation_type, sequence, binary_option_pass, binary_option_fail,
   active, create_uid, write_uid, create_date, write_date)
SELECT rel.id, 692, 'Deformidad o deterioro — Prueba', 'binary_selection', 70,
       'Sin deformidad o deterioro', 'Con deformidad o deterioro',
       true, 1, 1, NOW(), NOW()
FROM amunet_quality_parameter_product_rel rel
JOIN amunet_quality_check_parameter qcp ON qcp.id = rel.parameter_id AND qcp.code = 'MAVI-04'
JOIN product_product pp ON pp.product_tmpl_id = rel.product_tmpl_id
WHERE rel.active = true
  AND (pp.default_code LIKE 'DM%' OR pp.default_code LIKE 'DL%'
       OR pp.default_code LIKE 'DIAM%' OR pp.default_code LIKE 'DRAM%'
       OR pp.default_code LIKE 'DEMAM%')
  AND pp.default_code NOT IN ('DMPSA01','DMTSH02','DMFRT02')
  AND NOT EXISTS (
    SELECT 1 FROM amunet_quality_parameter_specification_config sc2
    WHERE sc2.product_parameter_rel_id = rel.id AND sc2.active = true AND sc2.sequence = 70
  );
