-- ============================================================
-- CORRECCIÓN DE DATOS — CAMBIO DE SERIAL INY → DIS (Dispensador)
-- Área: ensayo | Autor: Jorge Simarron / Agente ensayo
-- Fecha: 2026-06-08
-- Aprobación requerida: Fernando Ruiz o Mery (desarrollo)
-- ============================================================
-- QUÉ HACE:
--   Cambia la familia INY por DIS en el equipo Dispensador:
--   1. Serial del equipo: PRO/INY/01 → PRO/DIS/01
--   2. Nombre del expediente: EXP-CAL/INY/01 → EXP-CAL/DIS/01
--   3. Códigos de protocolo y reporte de las 4 calificaciones
--      (cd, ci, co, ce): reemplaza INY por DIS
-- ============================================================

BEGIN;

UPDATE amunet_equipment
SET serial_number = 'PRO/DIS/01'
WHERE serial_number = 'PRO/INY/01';

UPDATE amunet_equipment_expediente exp
SET name = 'EXP-CAL/DIS/01', write_date = NOW()
FROM amunet_equipment eq
WHERE exp.equipment_id = eq.id AND eq.serial_number = 'PRO/DIS/01';

UPDATE amunet_equipment_calificacion cal
SET protocol_code = REPLACE(cal.protocol_code, 'INY', 'DIS'),
    report_code   = REPLACE(cal.report_code,   'INY', 'DIS'),
    write_date    = NOW()
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
WHERE cal.expediente_id = exp.id AND eq.serial_number = 'PRO/DIS/01';

-- Verificación
SELECT eq.serial_number, exp.name, cal.qual_type, cal.protocol_code, cal.report_code
FROM amunet_equipment eq
JOIN amunet_equipment_expediente exp ON exp.equipment_id = eq.id
JOIN amunet_equipment_calificacion cal ON cal.expediente_id = exp.id
WHERE eq.serial_number = 'PRO/DIS/01'
ORDER BY cal.qual_type;

COMMIT;
