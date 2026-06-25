-- ============================================================
-- BOM → COM: Bomba al vacío (CAL/BOM/02 → CAL/COM/02)
-- Área: ensayo | Autor: Jorge Simarrón / Agente ensayo
-- Fecha: 2026-06-25
-- ============================================================
-- La bomba al vacío y su vacuómetro pertenecen a la misma familia COM.
-- El vacuómetro ya es CAL/COM/02-1; la bomba debe ser CAL/COM/02.
-- Actualiza: serial_number, expediente name, códigos de calificación,
-- líneas FVA/MVA, y enlace padre-hijo.
-- ============================================================

BEGIN;

-- 1. Renombrar serial de la bomba
UPDATE amunet_equipment
SET serial_number = 'CAL/COM/02', write_uid = 70, write_date = NOW()
WHERE serial_number = 'CAL/BOM/02';

-- 2. Expediente: nombre computado+almacenado — actualizar manualmente
UPDATE amunet_equipment_expediente exp
SET name = 'EXP-CAL/COM/02', write_date = NOW()
FROM amunet_equipment eq
WHERE exp.equipment_id = eq.id AND eq.serial_number = 'CAL/COM/02';

-- 3. Códigos de calificación: BOM → COM
UPDATE amunet_equipment_calificacion cal
SET protocol_code = REPLACE(COALESCE(cal.protocol_code,''), 'BOM', 'COM'),
    report_code   = REPLACE(COALESCE(cal.report_code,''),   'BOM', 'COM'),
    write_date    = NOW()
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
WHERE cal.expediente_id = exp.id AND eq.serial_number = 'CAL/COM/02';

-- 4. Líneas de programa FVA
UPDATE amunet_calibration_program_line
SET identification_code = 'CAL/COM/02', write_date = NOW()
WHERE identification_code = 'CAL/BOM/02';

-- 5. Líneas de programa MVA
UPDATE amunet_maintenance_program_line
SET identification_code = 'CAL/COM/02', write_date = NOW()
WHERE identification_code = 'CAL/BOM/02';

-- 6. Enlazar vacuómetro como hijo de la bomba
UPDATE amunet_equipment
SET parent_equipment_id = (
      SELECT id FROM amunet_equipment WHERE serial_number = 'CAL/COM/02'
    ),
    write_uid = 70, write_date = NOW()
WHERE serial_number = 'CAL/COM/02-1';

-- ============================================================
-- VERIFICACIÓN
-- ============================================================
SELECT eq.serial_number,
       eq.name,
       parent.serial_number    AS padre,
       exp.name                AS expediente,
       cal.qual_type,
       cal.protocol_code,
       cal.report_code
FROM amunet_equipment eq
LEFT JOIN amunet_equipment parent ON parent.id = eq.parent_equipment_id
LEFT JOIN amunet_equipment_expediente exp ON exp.equipment_id = eq.id
LEFT JOIN amunet_equipment_calificacion cal ON cal.expediente_id = exp.id
WHERE eq.serial_number IN ('CAL/COM/02','CAL/COM/02-1')
ORDER BY eq.serial_number, cal.qual_type;

COMMIT;
