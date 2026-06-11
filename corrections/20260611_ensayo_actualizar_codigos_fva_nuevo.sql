-- ============================================================
-- ACTUALIZACIÓN DE CÓDIGOS DE EQUIPO — FVA-002 v2 (junio 2026)
-- Área: ensayo | Autor: Jorge Simarrón / Agente ensayo
-- Fecha: 2026-06-11
-- ============================================================
-- El programa FVA-002 fue actualizado por Jorge con nuevos códigos
-- de familia para dos equipos. Este script alinea los serial_number
-- en la base de datos con el FVA actualizado, lo que también corrige
-- automáticamente el nombre del expediente (campo computado desde serial).
--
-- CAMBIOS DEL FVA:
--   1. Congelador:       CAL/CGR/01  →  CAL/CON/01
--   2. Cámara climática: EST/CLI/01  →  EST/CAM/01
--   3. Vacuómetro:       CAL/BOM/02-1 → CAL/COM/02-1  (según FVA)
-- ============================================================

BEGIN;

-- ============================================================
-- 1. CONGELADOR: CGR → CON
--    serial_number, expediente.name (computado), calificacion codes,
--    y líneas de programa FVA y MVA que usen el código viejo.
-- ============================================================
UPDATE amunet_equipment
SET serial_number = 'CAL/CON/01', write_uid = 70, write_date = NOW()
WHERE serial_number = 'CAL/CGR/01';

-- Expediente name (campo computado+almacenado; actualizar manualmente
-- porque el UPDATE SQL no dispara el trigger ORM)
UPDATE amunet_equipment_expediente exp
SET name = 'EXP-CAL/CON/01', write_date = NOW()
FROM amunet_equipment eq
WHERE exp.equipment_id = eq.id AND eq.serial_number = 'CAL/CON/01';

-- Códigos de calificación
UPDATE amunet_equipment_calificacion cal
SET protocol_code = REPLACE(COALESCE(cal.protocol_code,''), 'CGR', 'CON'),
    report_code   = REPLACE(COALESCE(cal.report_code,''),   'CGR', 'CON'),
    write_date    = NOW()
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
WHERE cal.expediente_id = exp.id AND eq.serial_number = 'CAL/CON/01';

-- Líneas de programa FVA
UPDATE amunet_calibration_program_line
SET identification_code = 'CAL/CON/01', write_date = NOW()
WHERE identification_code = 'CAL/CGR/01';

-- Líneas de programa MVA
UPDATE amunet_maintenance_program_line
SET identification_code = 'CAL/CON/01', write_date = NOW()
WHERE identification_code = 'CAL/CGR/01';

-- ============================================================
-- 2. CÁMARA CLIMÁTICA: CLI → CAM
-- ============================================================
UPDATE amunet_equipment
SET serial_number = 'EST/CAM/01', write_uid = 70, write_date = NOW()
WHERE serial_number = 'EST/CLI/01';

UPDATE amunet_equipment_expediente exp
SET name = 'EXP-CAL/CAM/01', write_date = NOW()
FROM amunet_equipment eq
WHERE exp.equipment_id = eq.id AND eq.serial_number = 'EST/CAM/01';

UPDATE amunet_equipment_calificacion cal
SET protocol_code = REPLACE(COALESCE(cal.protocol_code,''), 'CLI', 'CAM'),
    report_code   = REPLACE(COALESCE(cal.report_code,''),   'CLI', 'CAM'),
    write_date    = NOW()
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
WHERE cal.expediente_id = exp.id AND eq.serial_number = 'EST/CAM/01';

UPDATE amunet_calibration_program_line
SET identification_code = 'EST/CAM/01', write_date = NOW()
WHERE identification_code = 'EST/CLI/01';

UPDATE amunet_maintenance_program_line
SET identification_code = 'EST/CAM/01', write_date = NOW()
WHERE identification_code = 'EST/CLI/01';

-- ============================================================
-- 3. VACUÓMETRO: BOM/02-1 → COM/02-1  (FVA v2 usa CAL/COM/02-1)
--    Nota: la BOMBA (padre) se queda como CAL/BOM/02.
--    Solo el vacuómetro cambia de código.
-- ============================================================
UPDATE amunet_equipment
SET serial_number = 'CAL/COM/02-1', write_uid = 70, write_date = NOW()
WHERE serial_number = 'CAL/BOM/02-1';

-- (El vacuómetro no tiene expediente propio; es hijo de la bomba)
UPDATE amunet_calibration_program_line
SET identification_code = 'CAL/COM/02-1', write_date = NOW()
WHERE identification_code = 'CAL/BOM/02-1';

UPDATE amunet_maintenance_program_line
SET identification_code = 'CAL/COM/02-1', write_date = NOW()
WHERE identification_code = 'CAL/BOM/02-1';

-- ============================================================
-- VERIFICACIÓN
-- ============================================================
SELECT eq.serial_number,
       eq.name,
       exp.name  AS expediente,
       cal.protocol_code,
       cal.report_code
FROM amunet_equipment eq
LEFT JOIN amunet_equipment_expediente exp ON exp.equipment_id = eq.id
LEFT JOIN amunet_equipment_calificacion cal ON cal.expediente_id = exp.id
WHERE eq.serial_number IN ('CAL/CON/01','EST/CAM/01','CAL/COM/02-1','CAL/BOM/02')
ORDER BY eq.serial_number, cal.qual_type;

COMMIT;
