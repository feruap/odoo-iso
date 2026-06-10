-- ============================================================
-- ALINEACIÓN COMPLETA DE EQUIPOS CON PROGRAMA FVA 2026
-- Área: ensayo | Autor: Jorge Simarrón / Agente ensayo
-- Fecha: 2026-06-10
-- Aprobación requerida: Fernando Ruiz o Mery (desarrollo)
-- ============================================================
-- QUÉ HACE:
--   1. Crea 20 equipos nuevos (VAL/, micropipetas faltantes, DES/FUE/01,
--      CAL/BOM/02 y CAL/BOM/02-1)
--   2. Elimina 22 equipos que no están en FVA ni tienen expediente
--   3. Alinea calibration_required con el programa FVA
--   4. Agrega equipos faltantes al programa FVA (program_id = FVA-002 2026)
--   5. Corrige códigos de expedientes: CGR→CON, CLI→CAM
--   6. Crea expediente EXP-CAL/BOM/02 para la bomba al vacío
-- ============================================================

BEGIN;

-- ============================================================
-- 1. CREAR EQUIPOS NUEVOS (solo si no existen)
-- ============================================================
INSERT INTO amunet_equipment
  (name, serial_number, department, state,
   calibration_required, maintenance_required, is_deseable,
   has_calibratable_children,
   create_uid, write_uid, create_date, write_date)
VALUES
  ('Data logger',    'VAL/DTL/01',  'VALIDACIÓN',         'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Flexómetro',     'VAL/FLX/01',  'VALIDACIÓN',         'active', false, true,  false, false, 70,70,NOW(),NOW()),
  ('Nivel de gota',  'VAL/NLG/01',  'VALIDACIÓN',         'active', false, true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'PRO/MIC/09',  'SOLUCIONES',         'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'PRO/MIC/10',  'SOLUCIONES',         'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'CAL/MIC/04',  'CONTROL DE CALIDAD', 'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'CAL/MIC/05',  'CONTROL DE CALIDAD', 'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'CAL/MIC/07',  'CONTROL DE CALIDAD', 'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'CAL/MIC/08',  'CONTROL DE CALIDAD', 'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'CAL/MIC/09',  'CONTROL DE CALIDAD', 'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'CAL/MIC/10',  'CONTROL DE CALIDAD', 'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'DES/MIC/05',  'DESARROLLO',         'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'DES/MIC/06',  'DESARROLLO',         'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'DES/MIC/07',  'DESARROLLO',         'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'DES/MIC/08',  'DESARROLLO',         'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'DES/MIC/09',  'DESARROLLO',         'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Micropipeta',    'DES/MIC/10',  'DESARROLLO',         'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Fuente de poder','DES/FUE/01',  'DESARROLLO',         'active', true,  true,  false, false, 70,70,NOW(),NOW()),
  ('Bomba al vacío', 'CAL/BOM/02',  'CONTROL DE CALIDAD', 'active', false, true,  false, true,  70,70,NOW(),NOW()),
  ('Vacuómetro',     'CAL/BOM/02-1','CONTROL DE CALIDAD', 'active', true,  true,  false, false, 70,70,NOW(),NOW())
ON CONFLICT (serial_number) DO NOTHING;

-- ============================================================
-- 2. ELIMINAR 22 EQUIPOS FUERA DE FVA Y SIN EXPEDIENTE
-- ============================================================
DELETE FROM amunet_equipment
WHERE serial_number IN (
  'CAL/AGI/01','CAL/AUT/01','CAL/BAL/01','CAL/CAM/01','CAL/CCL/01',
  'CAL/CEN/01','CAL/CER/01','CAL/COR/01','CAL/ESP/01','CAL/HER/01',
  'CAL/HMZ/01','CAL/HOR/01','CAL/INC/01','CAL/LMP/01','CAL/MMP/01',
  'CAL/NAN/01',
  'DES/BAL/01','DES/COH/01','DES/ESP/01',
  'PRO/LMP/01','PRO/LMP/02','PRO/SDM/01'
);

-- ============================================================
-- 3. CALIBRATION_REQUIRED = FALSE (no se calibran)
-- ============================================================
UPDATE amunet_equipment
SET calibration_required = false, write_uid = 70, write_date = NOW()
WHERE serial_number IN (
  'PRO/SEL/01','PRO/IMP/01','CAL/BOM/02',
  'PRO/SEC/01','PRO/BOM/01','PRO/DIS/01',
  'PRO/COH/01','PRO/COT/01',
  'VAL/FLX/01','VAL/NLG/01','PRO/PCP/01'
);

-- ============================================================
-- 4. CALIBRATION_REQUIRED = TRUE (están en FVA)
-- ============================================================
UPDATE amunet_equipment
SET calibration_required = true, write_uid = 70, write_date = NOW()
WHERE serial_number IN (
  'PRO/TER/05','ALM/TER/01','ALP/TER/01','ALT/TER/01',
  'CAL/DTL/01','CAL/REG/01','CAL/TER/01',
  'PRO/TER/04','EST/TER/01','EST/TER/02',
  'PRO/TER/02','PRO/TER/03','PRO/PES/01','PRO/TER/01',
  'PRO/AGI/01','PRO/CEN/01'
);

-- ============================================================
-- 5. AGREGAR AL PROGRAMA FVA (FVA-002 2026)
--    Identifica el programa por nombre y año para portabilidad
-- ============================================================
DO $$
DECLARE v_prog_id INT;
BEGIN
  SELECT id INTO v_prog_id FROM amunet_calibration_program
  WHERE name ILIKE '%FVA-002%' AND year = 2026 LIMIT 1;

  INSERT INTO amunet_calibration_program_line
    (program_id, equipment_id, fva_equipment_name, identification_code,
     service_type, program_status, match_state, review_state,
     create_uid, write_uid, create_date, write_date)
  SELECT v_prog_id, e.id, e.name, e.serial_number,
    'calibracion', 'p', 'mismatch', 'pending',
    70, 70, NOW(), NOW()
  FROM amunet_equipment e
  WHERE e.serial_number IN (
    'PRO/AGI/01','PRO/CEN/01',
    'VAL/DTL/01',
    'PRO/MIC/09','PRO/MIC/10',
    'CAL/MIC/04','CAL/MIC/05','CAL/MIC/07','CAL/MIC/08','CAL/MIC/09','CAL/MIC/10',
    'DES/MIC/05','DES/MIC/06','DES/MIC/07','DES/MIC/08','DES/MIC/09','DES/MIC/10',
    'DES/FUE/01','CAL/BOM/02-1',
    'CAL/CNM/03','PRO/TER/05'
  )
  AND NOT EXISTS (
    SELECT 1 FROM amunet_calibration_program_line pl
    WHERE pl.equipment_id = e.id AND pl.program_id = v_prog_id
  );
END $$;

-- ============================================================
-- 6. CORREGIR CÓDIGOS DE EXPEDIENTES
-- ============================================================
-- Congelador: CGR → CON
UPDATE amunet_equipment_expediente exp
SET name = 'EXP-CAL/CON/01', write_date = NOW()
FROM amunet_equipment eq
WHERE exp.equipment_id = eq.id AND eq.serial_number = 'CAL/CGR/01'
  AND exp.name = 'EXP-CAL/CGR/01';

UPDATE amunet_equipment_calificacion cal
SET protocol_code = REPLACE(cal.protocol_code, 'CGR', 'CON'),
    report_code   = REPLACE(cal.report_code,   'CGR', 'CON'),
    write_date    = NOW()
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
WHERE cal.expediente_id = exp.id AND eq.serial_number = 'CAL/CGR/01'
  AND cal.protocol_code LIKE '%CGR%';

-- Cámara climática: CLI → CAM
UPDATE amunet_equipment_expediente exp
SET name = 'EXP-CAL/CAM/01', write_date = NOW()
FROM amunet_equipment eq
WHERE exp.equipment_id = eq.id AND eq.serial_number = 'EST/CLI/01'
  AND exp.name = 'EXP-CAL/CLI/01';

UPDATE amunet_equipment_calificacion cal
SET protocol_code = REPLACE(cal.protocol_code, 'CLI', 'CAM'),
    report_code   = REPLACE(cal.report_code,   'CLI', 'CAM'),
    write_date    = NOW()
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
WHERE cal.expediente_id = exp.id AND eq.serial_number = 'EST/CLI/01'
  AND cal.protocol_code LIKE '%CLI%';

-- ============================================================
-- 7. CREAR EXPEDIENTE BOMBA AL VACÍO (CAL/BOM/02)
-- ============================================================
INSERT INTO amunet_equipment_expediente
    (equipment_id, state, name, create_uid, write_uid, create_date, write_date)
SELECT e.id, 'vigente', 'EXP-CAL/BOM/02', 70, 70, NOW(), NOW()
FROM amunet_equipment e
WHERE e.serial_number = 'CAL/BOM/02'
AND NOT EXISTS (
    SELECT 1 FROM amunet_equipment_expediente x WHERE x.equipment_id = e.id
);

INSERT INTO amunet_equipment_calificacion
    (expediente_id, qual_type, result, protocol_code, report_code,
     protocol_date, report_date, responsible_id,
     create_uid, write_uid, create_date, write_date)
SELECT exp.id, t.qual_type, 'aprobado',
    'P' || UPPER(t.qual_type) || 'BOM-02',
    'R' || UPPER(t.qual_type) || 'BOM-02',
    'AGO/2024', 'SEP/2024', 70, 70, 70, NOW(), NOW()
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
CROSS JOIN (VALUES ('cd'),('ci'),('co'),('ce')) AS t(qual_type)
WHERE eq.serial_number = 'CAL/BOM/02'
AND NOT EXISTS (
    SELECT 1 FROM amunet_equipment_calificacion c WHERE c.expediente_id = exp.id
);

-- ============================================================
-- VERIFICACIÓN FINAL
-- ============================================================
SELECT
  (SELECT COUNT(*) FROM amunet_equipment)                                        AS total_equipos,
  (SELECT COUNT(*) FROM amunet_equipment WHERE department = 'VALIDACIÓN')        AS val_equipos,
  (SELECT COUNT(*) FROM amunet_calibration_program_line pl
    JOIN amunet_calibration_program cp ON cp.id = pl.program_id
    WHERE cp.year = 2026)                                                         AS total_fva,
  (SELECT COUNT(*) FROM amunet_equipment_expediente)                             AS total_expedientes,
  (SELECT COUNT(*) FROM amunet_equipment
    WHERE calibration_required = true
      AND NOT EXISTS (SELECT 1 FROM amunet_calibration_program_line pl
        JOIN amunet_calibration_program cp ON cp.id = pl.program_id
        WHERE pl.equipment_id = amunet_equipment.id AND cp.year = 2026)
      AND (is_deseable IS NULL OR is_deseable = false))                           AS equipos_cola_fuera_fva;

COMMIT;
