-- ============================================================
-- CORRECCIÓN DE DATOS — RESPONSABLE EN EXPEDIENTES DE CALIFICACIÓN
-- Área: ensayo | Autor: Jorge Simarron / Agente ensayo
-- Fecha: 2026-06-08
-- Aprobación requerida: Fernando Ruiz o Mery (desarrollo)
-- ============================================================
-- QUÉ HACE:
--   Los 18 expedientes de calificación y sus 72 calificaciones
--   quedaron registrados con Fernando (uid=67) como creador y
--   responsable. El responsable correcto es Jorge Simarron
--   (uid=70, ensayo@amunet.com.mx), quien dirige el área.
--   Este script corrige create_uid, write_uid y responsible_id.
-- ============================================================

BEGIN;

-- Corregir expedientes (create_uid y write_uid)
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

-- Corregir calificaciones (responsible_id, create_uid, write_uid)
UPDATE amunet_equipment_calificacion
SET responsible_id = 70,
    create_uid     = 70,
    write_uid      = 70
WHERE create_uid = 67
  AND expediente_id IN (
      SELECT exp.id
      FROM amunet_equipment_expediente exp
      JOIN amunet_equipment eq ON eq.id = exp.equipment_id
      WHERE eq.serial_number IN (
          'PRO/AGI/01','PRO/AGO/01','PRO/AMO/01','PRO/BAL/01',
          'PRO/CEN/01','CAL/CGR/01','EST/CLI/01','PRO/COH/01',
          'PRO/COT/01','PRO/ESP/01','PRO/HOR/01','PRO/HOR/02',
          'PRO/HOR/03','PRO/IMP/01','PRO/INY/01','ALM/REF/01',
          'PRO/SEC/01','PRO/SEL/01'
      )
  );

-- Verificación
SELECT
    eq.serial_number,
    exp.state,
    (SELECT login FROM res_users WHERE id = exp.create_uid)  AS creado_por,
    (SELECT login FROM res_users WHERE id = cal.responsible_id) AS responsable
FROM amunet_equipment_expediente exp
JOIN amunet_equipment eq ON eq.id = exp.equipment_id
JOIN amunet_equipment_calificacion cal ON cal.expediente_id = exp.id AND cal.qual_type = 'cd'
ORDER BY eq.serial_number;

COMMIT;
