-- ============================================================
-- PROGRAMA ANUAL DE MANTENIMIENTO PREVENTIVO MVA 2026
-- Área: ensayo | Autor: Jorge Simarrón / Agente ensayo
-- Fecha: 2026-06-10
-- Fuente: MVA-001 a MVA-011 (carpeta para agente.ia)
-- Correcciones:
--   PRO/INY/01 → PRO/DIS/01 (sistema es la fuente de verdad)
--   PRO/CGR/01 → CAL/CGR/01 (typo en MVA-011)
-- ============================================================

BEGIN;

-- Tabla temporal con las actividades
CREATE TEMP TABLE mva_lines (
  mva_name    TEXT,
  equip_code  TEXT,
  equip_name  TEXT,
  month       TEXT,
  activity    TEXT
) ON COMMIT DROP;

INSERT INTO mva_lines VALUES
  -- MVA-001 Almacén de Materia Prima
  ('MVA-001 Almacén de Materia Prima', 'ALM/REF/01', 'Refrigerador',             '06', 'LP'),
  ('MVA-001 Almacén de Materia Prima', 'ALM/REF/01', 'Refrigerador',             '12', 'LP'),
  ('MVA-001 Almacén de Materia Prima', 'ALM/TER/01', 'Termohigrómetro',          '06', 'RP'),
  -- MVA-002 Soluciones
  ('MVA-002 Soluciones', 'PRO/AGI/01', 'Agitador magnético con calefacción',    '06', 'GP'),
  ('MVA-002 Soluciones', 'PRO/AGO/01', 'Agitador orbital',                      '06', 'GP'),
  ('MVA-002 Soluciones', 'PRO/AMO/01', 'Analizador multiparamétrico',            '06', 'GP'),
  ('MVA-002 Soluciones', 'PRO/BAL/01', 'Balanza analítica',                     '06', 'GP'),
  ('MVA-002 Soluciones', 'PRO/CEN/01', 'Centrífuga',                            '06', 'GP'),
  ('MVA-002 Soluciones', 'PRO/ESP/01', 'Espectrofotómetro',                     '06', 'GP'),
  ('MVA-002 Soluciones', 'PRO/ESP/01', 'Espectrofotómetro',                     '06', 'LP'),
  ('MVA-002 Soluciones', 'PRO/HOR/01', 'Horno',                                 '06', 'GP'),
  ('MVA-002 Soluciones', 'PRO/TER/01', 'Termohigrómetro',                       '06', 'RP'),
  -- MVA-003 Lectura y Pretratamiento
  ('MVA-003 Lectura y Pretratamiento', 'PRO/AGO/01', 'Agitador orbital',         '06', 'GP'),
  ('MVA-003 Lectura y Pretratamiento', 'PRO/ESP/01', 'Espectrofotómetro',        '06', 'GP'),
  ('MVA-003 Lectura y Pretratamiento', 'PRO/ESP/01', 'Espectrofotómetro',        '06', 'LP'),
  ('MVA-003 Lectura y Pretratamiento', 'PRO/HOR/01', 'Horno',                    '06', 'GP'),
  -- MVA-004 Inyección (PRO/INY/01 → PRO/DIS/01)
  ('MVA-004 Inyección', 'PRO/BOM/01', 'Compresor',       '04', 'CP'),
  ('MVA-004 Inyección', 'PRO/BOM/01', 'Compresor',       '06', 'GP'),
  ('MVA-004 Inyección', 'PRO/BOM/01', 'Compresor',       '08', 'CP'),
  ('MVA-004 Inyección', 'PRO/BOM/01', 'Compresor',       '12', 'CP'),
  ('MVA-004 Inyección', 'PRO/DIS/01', 'Dispensador',     '06', 'FP'),
  ('MVA-004 Inyección', 'PRO/DIS/01', 'Dispensador',     '12', 'FP'),
  ('MVA-004 Inyección', 'PRO/HOR/02', 'Horno',           '06', 'GP'),
  ('MVA-004 Inyección', 'PRO/TER/02', 'Termohigrómetro', '06', 'RP'),
  -- MVA-005 Encartuchado
  ('MVA-005 Encartuchado', 'PRO/SEC/01', 'Selladora de cartuchos', '06', 'GP'),
  ('MVA-005 Encartuchado', 'PRO/SEC/01', 'Selladora de cartuchos', '12', 'GP'),
  ('MVA-005 Encartuchado', 'PRO/TER/04', 'Termohigrómetro',        '06', 'RP'),
  -- MVA-006 Laminado, Secado y Corte
  ('MVA-006 Laminado, Secado y Corte', 'PRO/COH/01', 'Cortadora de hojas', '06', 'GP'),
  ('MVA-006 Laminado, Secado y Corte', 'PRO/COH/01', 'Cortadora de hojas', '06', 'LP'),
  ('MVA-006 Laminado, Secado y Corte', 'PRO/COH/01', 'Cortadora de hojas', '12', 'LP'),
  ('MVA-006 Laminado, Secado y Corte', 'PRO/COT/01', 'Cortadora de tiras', '06', 'GP'),
  ('MVA-006 Laminado, Secado y Corte', 'PRO/COT/01', 'Cortadora de tiras', '06', 'LP'),
  ('MVA-006 Laminado, Secado y Corte', 'PRO/COT/01', 'Cortadora de tiras', '12', 'LP'),
  ('MVA-006 Laminado, Secado y Corte', 'PRO/HOR/03', 'Horno',              '06', 'GP'),
  ('MVA-006 Laminado, Secado y Corte', 'PRO/TER/03', 'Termohigrómetro',    '06', 'RP'),
  -- MVA-007 Acondicionado 1
  ('MVA-007 Acondicionado 1', 'PRO/SEL/01', 'Selladora de bolsas', '06', 'GP'),
  ('MVA-007 Acondicionado 1', 'PRO/SEL/01', 'Selladora de bolsas', '12', 'GP'),
  ('MVA-007 Acondicionado 1', 'PRO/TER/05', 'Termohigrómetro',     '06', 'RP'),
  -- MVA-008 Acondicionado 2
  ('MVA-008 Acondicionado 2', 'PRO/IMP/01', 'Impresora láser', '06', 'GP'),
  ('MVA-008 Acondicionado 2', 'PRO/IMP/01', 'Impresora láser', '12', 'GP'),
  -- MVA-009 Almacén Temporal de PT
  ('MVA-009 Almacén Temporal de PT', 'ALT/TER/01', 'Termohigrómetro', '06', 'RP'),
  -- MVA-010 Estabilidad
  ('MVA-010 Estabilidad', 'EST/CLI/01', 'Cámara climática',  '06', 'GP'),
  ('MVA-010 Estabilidad', 'EST/CLI/01', 'Cámara climática',  '06', 'LP'),
  ('MVA-010 Estabilidad', 'EST/CLI/01', 'Cámara climática',  '06', 'FP'),
  ('MVA-010 Estabilidad', 'EST/CLI/01', 'Cámara climática',  '12', 'LP'),
  ('MVA-010 Estabilidad', 'EST/CLI/01', 'Cámara climática',  '12', 'FP'),
  ('MVA-010 Estabilidad', 'EST/TER/01', 'Termohigrómetro',   '06', 'RP'),
  ('MVA-010 Estabilidad', 'EST/TER/02', 'Termohigrómetro',   '06', 'RP'),
  -- MVA-011 Control de Calidad (PRO/CGR/01 → CAL/CGR/01)
  ('MVA-011 Control de Calidad', 'CAL/BOM/01', 'Bomba de vacío',      '06', 'GP'),
  ('MVA-011 Control de Calidad', 'CAL/CGR/01', 'Congelador',          '06', 'GP'),
  ('MVA-011 Control de Calidad', 'CAL/CGR/01', 'Congelador',          '06', 'LP'),
  ('MVA-011 Control de Calidad', 'CAL/CGR/01', 'Congelador',          '12', 'LP'),
  ('MVA-011 Control de Calidad', 'CAL/MIE/01', 'Micrómetro Exterior', '06', 'GP'),
  ('MVA-011 Control de Calidad', 'CAL/REG/01', 'Regla',               '06', 'GP'),
  ('MVA-011 Control de Calidad', 'CAL/TER/01', 'Termohigrómetro',     '06', 'RP');

-- Crear el programa
DO $$
DECLARE
  v_prog_id  INT;
BEGIN
  INSERT INTO amunet_maintenance_program
    (name, year, state, create_uid, write_uid, create_date, write_date)
  VALUES
    ('MVA 2026 — Programa Anual de Mantenimiento Preventivo', 2026, 'draft',
     70, 70, NOW(), NOW())
  RETURNING id INTO v_prog_id;

  -- Insertar líneas enlazando con equipos cuando existen
  INSERT INTO amunet_maintenance_program_line
    (program_id, mva_equipment_name, identification_code, area_name,
     month, activity_type, equipment_id, match_state, program_status,
     create_uid, write_uid, create_date, write_date)
  SELECT
    v_prog_id,
    m.equip_name,
    m.equip_code,
    m.mva_name,
    m.month,
    m.activity,
    e.id,
    CASE WHEN e.id IS NOT NULL THEN 'matched' ELSE 'missing' END,
    'p',
    70, 70, NOW(), NOW()
  FROM mva_lines m
  LEFT JOIN amunet_equipment e ON e.serial_number = m.equip_code;
END $$;

-- Verificación
SELECT
  COUNT(*)                                                        AS total_lineas,
  COUNT(*) FILTER (WHERE l.match_state = 'matched')              AS encontrados,
  COUNT(*) FILTER (WHERE l.match_state = 'missing')              AS faltantes,
  STRING_AGG(DISTINCT l.identification_code, ', ')
    FILTER (WHERE l.match_state = 'missing')                     AS codigos_faltantes
FROM amunet_maintenance_program_line l
JOIN amunet_maintenance_program p ON p.id = l.program_id
WHERE p.year = 2026;

COMMIT;
