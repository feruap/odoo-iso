-- ============================================================
-- CORRECCIÓN DE DATOS — EXPEDIENTES DE CALIFICACIÓN EN PRODUCCIÓN
-- Área: ensayo | Autor: Jorge Simarron / Agente ensayo
-- Fecha: 2026-06-08
-- Aprobación requerida: Fernando Ruiz o Mery (desarrollo)
-- ============================================================
-- QUÉ HACE:
--   1. Corrige responsable: Fernando (uid=67) → Jorge Simarron (uid=70)
--      en los 18 expedientes y 72 calificaciones del área de ensayo.
--   2. Genera los códigos de protocolo y reporte (PCDAGI-01, RCDAGI-01, etc.)
--      que quedaron vacíos al insertar con SQL.
--   3. Asigna fechas estándar: protocolo = AGO/2024, reporte = SEP/2024
--      (fecha real de las calificaciones del área, confirmada por Jorge).
-- ============================================================

BEGIN;

-- 1. Corregir responsable en expedientes
UPDATE amunet_equipment_expediente
SET create_uid = 70,
    write_uid  = 70
WHERE create_uid = 67
  AND equipment_id IN (
      SELECT id FROM amunet_equipment
      WHERE serial_number IN (
          'PRO/AGI/01','PRO/AGO/01','PRO/AMO/01','PRO/BAL/01',
          'PRO/CEN/01','CAL/CGR/01','EST/CLI/01','PRO/COH/01',
          'PRO/COT/01','PRO/ESP/01','PRO/HOR/01','PRO/HOR/02',
          'PRO/HOR/03','PRO/IMP/01','PRO/INY/01','ALM/REF/01',
          'PRO/SEC/01','PRO/SEL/01'
      )
  );

-- 2. Corregir responsable en calificaciones + generar códigos + fechas
UPDATE amunet_equipment_calificacion cal
SET responsible_id = 70,
    create_uid     = 70,
    write_uid      = 70,
    protocol_code  = 'P' || UPPER(cal.qual_type) || split_part(eq.serial_number,'/',2) || '-' || split_part(eq.serial_number,'/',3),
    report_code    = 'R' || UPPER(cal.qual_type) || split_part(eq.serial_number,'/',2) || '-' || split_part(eq.serial_number,'/',3),
    protocol_date  = COALESCE(NULLIF(cal.protocol_date,''), 'AGO/2024'),
    report_date    = COALESCE(NULLIF(cal.report_date,''), 'SEP/2024')
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
WHERE cal.expediente_id = exp.id
  AND eq.serial_number IN (
      'PRO/AGI/01','PRO/AGO/01','PRO/AMO/01','PRO/BAL/01',
      'PRO/CEN/01','CAL/CGR/01','EST/CLI/01','PRO/COH/01',
      'PRO/COT/01','PRO/ESP/01','PRO/HOR/01','PRO/HOR/02',
      'PRO/HOR/03','PRO/IMP/01','PRO/INY/01','ALM/REF/01',
      'PRO/SEC/01','PRO/SEL/01'
  );

-- Verificación final
SELECT
    eq.serial_number,
    exp.state,
    (SELECT login FROM res_users WHERE id = exp.create_uid) AS creado_por,
    cal.qual_type,
    cal.protocol_code,
    cal.report_code,
    cal.protocol_date,
    cal.report_date,
    (SELECT login FROM res_users WHERE id = cal.responsible_id) AS responsable
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
JOIN amunet_equipment_calificacion cal ON cal.expediente_id = exp.id AND cal.qual_type = 'cd'
ORDER BY eq.serial_number;

COMMIT;
