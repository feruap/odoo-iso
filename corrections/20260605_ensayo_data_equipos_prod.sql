-- ============================================================
-- MIGRACIÓN DE DATOS — EQUIPOS / CALIBRACIÓN
-- Área: ensayo | Autor: Jorge Simarron / Agente ensayo
-- Fecha: 2026-06-05
-- Aprobación requerida: Fernando Ruiz o Mery (desarrollo)
-- ============================================================
-- QUÉ HACE:
--   1. Corrige nombre de departamento: LECTURA Y SECADO → LECTURA Y PRETRATAMIENTO
--   2. Corrige seriales: PRO/AGI/02 → PRO/AGI/01 | PRO/CEN/02 → PRO/CEN/01
--   3. Inicializa is_deseable=false para todos los oficiales (era NULL)
--   4. Marca 31 equipos como is_deseable=true (libre uso, sin programa)
--      y les quita calibration_required y maintenance_required
--   5. Crea 18 expedientes de calificación en estado "vigente"
--      con 4 calificaciones aprobadas cada uno (72 total)
--   6. Activa el parámetro de período de gracia: 2026-07-02
-- ============================================================

BEGIN;

-- 1. Corregir departamento
UPDATE amunet_equipment
SET department = 'LECTURA Y PRETRATAMIENTO'
WHERE department = 'LECTURA Y SECADO';

-- 2. Corregir seriales
UPDATE amunet_equipment SET serial_number = 'PRO/AGI/01' WHERE serial_number = 'PRO/AGI/02';
UPDATE amunet_equipment SET serial_number = 'PRO/CEN/01' WHERE serial_number = 'PRO/CEN/02';

-- 3. Inicializar is_deseable=false donde es NULL
UPDATE amunet_equipment SET is_deseable = false WHERE is_deseable IS NULL;

-- 4. Marcar deseables (por serial — independiente del ID)
UPDATE amunet_equipment
SET is_deseable = true,
    calibration_required = false,
    maintenance_required = false
WHERE serial_number IN (
    'CAL/EQT/01',
    'DES/AGP/01', 'DES/AUT/01', 'DES/BIO/01', 'DES/CAM/01',
    'DES/CEH/01', 'DES/CER/01', 'DES/CEV/01', 'DES/FUP/01',
    'DES/FUP/02', 'DES/INA/01', 'DES/INP/01', 'DES/LIO/01',
    'DES/MIO/01', 'DES/MIO/02', 'DES/MNC/01', 'DES/MXR/01',
    'DES/NAN/01', 'DES/NGC/01', 'DES/PHM/01', 'DES/REC/01',
    'DES/SFT/01', 'DES/SON/01', 'DES/TBL/01', 'DES/TER/PF/01',
    'DES/TER/TR/01', 'DES/TLU/01', 'DES/UCG/01', 'DES/VOR/01',
    'PRO/MNC/02', 'PRO/VOR/02'
);

-- 5. Crear expedientes de calificación (vigente) para los 18 equipos del programa
INSERT INTO amunet_equipment_expediente
    (equipment_id, state, create_uid, write_uid, create_date, write_date)
SELECT
    e.id,
    'vigente',
    67, 67, NOW(), NOW()
FROM amunet_equipment e
WHERE e.serial_number IN (
    'PRO/AGI/01', 'PRO/AGO/01', 'PRO/AMO/01', 'PRO/BAL/01',
    'PRO/CEN/01', 'CAL/CGR/01', 'EST/CLI/01', 'PRO/COH/01',
    'PRO/COT/01', 'PRO/ESP/01', 'PRO/HOR/01', 'PRO/HOR/02',
    'PRO/HOR/03', 'PRO/IMP/01', 'PRO/INY/01', 'ALM/REF/01',
    'PRO/SEC/01', 'PRO/SEL/01'
)
AND NOT EXISTS (
    SELECT 1 FROM amunet_equipment_expediente x WHERE x.equipment_id = e.id
);

-- 5b. Crear las 4 calificaciones por expediente (cd, ci, co, ce)
INSERT INTO amunet_equipment_calificacion
    (expediente_id, qual_type, result, responsible_id, create_uid, write_uid, create_date, write_date)
SELECT
    exp.id,
    t.qual_type,
    'aprobado',
    67, 67, 67, NOW(), NOW()
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
CROSS JOIN (VALUES ('cd'), ('ci'), ('co'), ('ce')) AS t(qual_type)
WHERE eq.serial_number IN (
    'PRO/AGI/01', 'PRO/AGO/01', 'PRO/AMO/01', 'PRO/BAL/01',
    'PRO/CEN/01', 'CAL/CGR/01', 'EST/CLI/01', 'PRO/COH/01',
    'PRO/COT/01', 'PRO/ESP/01', 'PRO/HOR/01', 'PRO/HOR/02',
    'PRO/HOR/03', 'PRO/IMP/01', 'PRO/INY/01', 'ALM/REF/01',
    'PRO/SEC/01', 'PRO/SEL/01'
)
AND NOT EXISTS (
    SELECT 1 FROM amunet_equipment_calificacion c WHERE c.expediente_id = exp.id
);

-- 6. Parámetro de período de gracia
INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date)
VALUES ('amunet.calibration.grace.deadline', '2026-07-02', 67, 67, NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = '2026-07-02', write_date = NOW();

-- Verificación final
SELECT
    (SELECT COUNT(*) FROM amunet_equipment WHERE is_deseable = true)          AS deseables,
    (SELECT COUNT(*) FROM amunet_equipment WHERE calibration_required = true AND is_deseable = false) AS calibrables_oficiales,
    (SELECT COUNT(*) FROM amunet_equipment_expediente WHERE state = 'vigente') AS expedientes_vigentes,
    (SELECT COUNT(*) FROM amunet_equipment_calificacion WHERE result = 'aprobado') AS cals_aprobadas,
    (SELECT value FROM ir_config_parameter WHERE key = 'amunet.calibration.grace.deadline') AS gracia,
    (SELECT COUNT(*) FROM amunet_equipment WHERE department = 'LECTURA Y PRETRATAMIENTO') AS dept_corregido;

COMMIT;
