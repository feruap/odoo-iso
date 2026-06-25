-- ============================================================
-- NUEVOS EQUIPOS — FVA-002 v3 (25-jun-2026)
-- Área: ensayo | Autor: Jorge Simarrón / Agente ensayo
-- Fecha: 2026-06-25
-- Fuente: FVA-002 Programa 2026 de calibración-caracterización
--         (versión actualizada en Nextcloud, 25-jun-2026)
-- ============================================================
-- QUÉ HACE:
--   1. Crea 5 equipos nuevos detectados en el FVA actualizado:
--        CAL/ESC/01   Escuadra                 CONTROL DE CALIDAD
--        DES/TER/01   Termohigrómetro          DESARROLLO
--        PRO/COM/01-1 Manómetro                SOLUCIONES
--        PRO/COM/01-2 Manómetro                SOLUCIONES
--        VAL/MCI/01   Medidor de luz           VALIDACIÓN
--   2. Los agrega al programa FVA-002 2026 (amunet_calibration_program_line)
--      para que aparezcan en la cola de calibración.
-- ============================================================

BEGIN;

-- ============================================================
-- 1. INSERTAR EQUIPOS NUEVOS (solo si no existen)
-- ============================================================
INSERT INTO amunet_equipment
  (name, serial_number, department, state,
   calibration_required, maintenance_required, is_deseable,
   has_calibratable_children,
   brand, model_name,
   create_uid, write_uid, create_date, write_date)
SELECT t.name, t.serial_number, t.department, 'active',
       true, true, false, false,
       t.brand, t.model_name,
       70, 70, NOW(), NOW()
FROM (VALUES
  ('Escuadra',          'CAL/ESC/01',   'CONTROL DE CALIDAD', NULL,         'KFBA10L87'),
  ('Termohigrómetro',   'DES/TER/01',   'DESARROLLO',         'HTC',        'HTC-1'),
  ('Manómetro',         'PRO/COM/01-1', 'SOLUCIONES',         'INSTRUTEK',  NULL),
  ('Manómetro',         'PRO/COM/01-2', 'SOLUCIONES',         'INSTRUTEK',  NULL),
  ('Medidor de luz',    'VAL/MCI/01',   'VALIDACIÓN',         'SNAKOL',     'SK-8201')
) AS t(name, serial_number, department, brand, model_name)
WHERE NOT EXISTS (
  SELECT 1 FROM amunet_equipment x WHERE x.serial_number = t.serial_number
);

-- ============================================================
-- 2. AGREGAR AL PROGRAMA FVA-002 2026
-- ============================================================
DO $$
DECLARE v_prog_id INT;
BEGIN
  SELECT id INTO v_prog_id
  FROM amunet_calibration_program
  WHERE name ILIKE '%FVA-002%' AND year = 2026
  LIMIT 1;

  IF v_prog_id IS NULL THEN
    RAISE NOTICE 'No se encontró el programa FVA-002 2026; saltando inserción de líneas.';
    RETURN;
  END IF;

  INSERT INTO amunet_calibration_program_line
    (program_id, equipment_id, fva_equipment_name, identification_code,
     service_type, program_status, match_state, review_state,
     create_uid, write_uid, create_date, write_date)
  SELECT v_prog_id, e.id, e.name, e.serial_number,
         'calibracion', 'p', 'matched', 'pending',
         70, 70, NOW(), NOW()
  FROM amunet_equipment e
  WHERE e.serial_number IN (
    'CAL/ESC/01', 'DES/TER/01',
    'PRO/COM/01-1', 'PRO/COM/01-2',
    'VAL/MCI/01'
  )
  AND NOT EXISTS (
    SELECT 1 FROM amunet_calibration_program_line pl
    WHERE pl.equipment_id = e.id AND pl.program_id = v_prog_id
  );

  RAISE NOTICE 'Líneas de programa FVA insertadas correctamente.';
END $$;

-- ============================================================
-- VERIFICACIÓN
-- ============================================================
SELECT eq.serial_number,
       eq.name,
       eq.department,
       eq.brand,
       eq.model_name              AS serial_fab,
       eq.calibration_required    AS cal,
       CASE WHEN pl.id IS NOT NULL THEN 'SÍ' ELSE 'NO' END AS en_fva
FROM amunet_equipment eq
LEFT JOIN amunet_calibration_program_line pl ON pl.equipment_id = eq.id
  AND pl.program_id = (
    SELECT id FROM amunet_calibration_program
    WHERE name ILIKE '%FVA-002%' AND year = 2026 LIMIT 1
  )
WHERE eq.serial_number IN (
  'CAL/ESC/01', 'DES/TER/01',
  'PRO/COM/01-1', 'PRO/COM/01-2',
  'VAL/MCI/01'
)
ORDER BY eq.serial_number;

COMMIT;
