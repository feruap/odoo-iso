-- ============================================================
-- CORRECCIÓN: Nombres de expedientes vacíos + código BOM en bomba
-- Área: ensayo | Autor: Jorge Simarrón / Agente ensayo
-- Fecha: 2026-06-11
-- Aplica en: PRODUCCIÓN (Main) después del deploy del 10-jun
-- ============================================================
-- PROBLEMA 1: "No aparecen todos los códigos de expedientes"
--   El campo name de amunet_equipment_expediente es computado+almacenado.
--   En Main los registros viejos tienen ese campo vacío porque Odoo solo
--   lo recomputa cuando cambia serial_number. Solución: llenarlo via SQL
--   para todos los expedientes con nombre vacío.
--
-- PROBLEMA 2: "Bomba al vacío muestra COM en vez de BOM"
--   El script FVA filtró por exp.name LIKE 'EXP-CAL/COM/%', que no coincidió
--   porque name estaba vacío. Resultado: nombre y códigos de calificación
--   de la bomba quedaron con COM. Se corrige aquí por serial_number.
-- ============================================================

BEGIN;

-- ============================================================
-- 1. RECALCULAR NOMBRE para todos los expedientes con nombre vacío
--    (fórmula idéntica al método _compute_name del modelo)
-- ============================================================
UPDATE amunet_equipment_expediente exp
SET name = 'EXP-CAL/'
         || split_part(eq.serial_number, '/', 2)
         || '/'
         || split_part(eq.serial_number, '/', 3),
    write_date = NOW()
FROM amunet_equipment eq
WHERE exp.equipment_id = eq.id
  AND (exp.name IS NULL OR exp.name = '' OR exp.name = 'EXP-CAL/--/--')
  AND eq.serial_number ~ '^[^/]+/[^/]+/[^/]+$';

-- ============================================================
-- 2. CONGELADOR (CAL/CGR/01) → código correcto: CON no CGR
-- ============================================================
UPDATE amunet_equipment_expediente exp
SET name = 'EXP-CAL/CON/01', write_date = NOW()
FROM amunet_equipment eq
WHERE exp.equipment_id = eq.id AND eq.serial_number = 'CAL/CGR/01';

UPDATE amunet_equipment_calificacion cal
SET protocol_code = REPLACE(COALESCE(cal.protocol_code,''), 'CGR', 'CON'),
    report_code   = REPLACE(COALESCE(cal.report_code,''),   'CGR', 'CON'),
    write_date    = NOW()
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
WHERE cal.expediente_id = exp.id AND eq.serial_number = 'CAL/CGR/01';

-- ============================================================
-- 3. CÁMARA CLIMÁTICA (EST/CLI/01) → código correcto: CAM no CLI
-- ============================================================
UPDATE amunet_equipment_expediente exp
SET name = 'EXP-CAL/CAM/01', write_date = NOW()
FROM amunet_equipment eq
WHERE exp.equipment_id = eq.id AND eq.serial_number = 'EST/CLI/01';

UPDATE amunet_equipment_calificacion cal
SET protocol_code = REPLACE(COALESCE(cal.protocol_code,''), 'CLI', 'CAM'),
    report_code   = REPLACE(COALESCE(cal.report_code,''),   'CLI', 'CAM'),
    write_date    = NOW()
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
WHERE cal.expediente_id = exp.id AND eq.serial_number = 'EST/CLI/01';

-- ============================================================
-- 4. BOMBA AL VACÍO (CAL/BOM/02) → código correcto: BOM no COM
-- ============================================================
UPDATE amunet_equipment_expediente exp
SET name = 'EXP-CAL/BOM/02', write_date = NOW()
FROM amunet_equipment eq
WHERE exp.equipment_id = eq.id AND eq.serial_number = 'CAL/BOM/02';

UPDATE amunet_equipment_calificacion cal
SET protocol_code = REPLACE(COALESCE(cal.protocol_code,''), 'COM', 'BOM'),
    report_code   = REPLACE(COALESCE(cal.report_code,''),   'COM', 'BOM'),
    write_date    = NOW()
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
WHERE cal.expediente_id = exp.id AND eq.serial_number = 'CAL/BOM/02';

-- ============================================================
-- VERIFICACIÓN FINAL
-- ============================================================
SELECT eq.serial_number,
       exp.name                              AS expediente,
       cal.qual_type,
       cal.protocol_code,
       cal.report_code
FROM amunet_equipment eq
JOIN amunet_equipment_expediente exp ON exp.equipment_id = eq.id
LEFT JOIN amunet_equipment_calificacion cal ON cal.expediente_id = exp.id
WHERE eq.serial_number IN ('CAL/CGR/01','EST/CLI/01','CAL/BOM/02')
ORDER BY eq.serial_number, cal.qual_type;

COMMIT;
