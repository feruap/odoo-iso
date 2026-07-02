-- ============================================================
-- DESEABLES — ampliación del catálogo (45 equipos nuevos)
-- Área: ensayo | Autor: Jorge Simarrón / Agente ensayo
-- Fecha: 2026-07-02
-- Fuente: Listado_equipos_deseables.docx (Nextcloud)
-- ============================================================
-- QUÉ HACE:
--   Inserta 45 equipos con is_deseable=TRUE.
--   Quedan fuera de la cola de calibración, programas FVA/MVA
--   y cualquier métrica de cumplimiento ISO.
--   No se modifica NINGÚN equipo oficial existente.
-- CODIFICACIÓN:
--   Regla 1 (primeras 3 letras) o Regla 2 (primera+media+última)
--   si ya existe el código en esa área.
--   Numeración: continúa después del último oficial en la misma área;
--   reinicia en /01 si es diferente área.
-- ============================================================

BEGIN;

INSERT INTO amunet_equipment
  (name, serial_number, department, state,
   calibration_required, maintenance_required, is_deseable,
   has_calibratable_children,
   create_uid, write_uid, create_date, write_date)
SELECT t.name, t.serial_number, t.department, 'active',
       false, false, true, false,
       70, 70, NOW(), NOW()
FROM (VALUES
  -- ── ALMACÉN DE MATERIA PRIMA ─────────────────────────────
  -- ALM/REF/01 oficial existe → continúa en /02
  ('Refrigerador',                      'ALM/REF/02',  'ALMACÉN DE MATERIA PRIMA'),

  -- ── SOLUCIONES ───────────────────────────────────────────
  -- PRO/AGI/01 oficial existe → continúa en /02, /03
  ('Agitador magnético con calefacción','PRO/AGI/02',  'SOLUCIONES'),
  ('Agitador magnético',                'PRO/AGI/03',  'SOLUCIONES'),
  -- Familias nuevas en SOLUCIONES → arrancan en /01
  ('Centrífuga Palm-series',            'PRO/PAL/01',  'SOLUCIONES'),
  ('Esterilizador',                     'PRO/EST/01',  'SOLUCIONES'),
  ('Congelador',                        'PRO/CON/01',  'SOLUCIONES'),
  -- COR: CON ya tomado por PRO/CON/01 → Regla 2 Controlador→COR (sin conflicto en PRO)
  ('Controlador de llenado',            'PRO/COR/01',  'SOLUCIONES'),
  -- PRO/MIC/01-10 oficiales → continúan en /11-/14
  ('Micropipeta',                       'PRO/MIC/11',  'SOLUCIONES'),
  ('Micropipeta',                       'PRO/MIC/12',  'SOLUCIONES'),
  ('Micropipeta',                       'PRO/MIC/13',  'SOLUCIONES'),
  ('Micropipeta',                       'PRO/MIC/14',  'SOLUCIONES'),

  -- ── LECTURA Y PRETRATAMIENTO ─────────────────────────────
  ('BIOBASE1000',                       'PRO/BIO/01',  'LECTURA Y PRETRATAMIENTO'),

  -- ── INYECCIÓN ────────────────────────────────────────────
  -- BIO ya tomado → BIODOT usa Regla 2: B+I+T? No: B-I-O-D-O-T (6 chars, pos 3=D) → BDT
  ('BIODOT XYZ3050',                    'PRO/BDT/01',  'INYECCIÓN'),
  ('GREEN SERIES / KINCO',              'PRO/GRE/01',  'INYECCIÓN'),
  -- COM ya existe en CAL → Compresor en PRO: COM libre en PRO, pero usa CRR
  -- (PRO/COM/01-1 y /01-2 son oficiales de Manómetro) → Compresor Regla 2: C+M+R?
  -- "Compresor": C-O-M-P-R-E-S-O-R (9 chars, pos 4=R) → COR ocupado por Controlador → CRR
  ('Compresor de aire',                 'PRO/CRR/01',  'INYECCIÓN'),
  -- REF libre en INYECCIÓN (área distinta a ALM) → reinicia /01
  ('Refrigerador',                      'PRO/REF/01',  'INYECCIÓN'),

  -- ── LAMINADO, SECADO Y CORTE ─────────────────────────────
  ('Laminadora manual',                 'PRO/LAM/01',  'LAMINADO, SECADO Y CORTE'),
  ('Deshumificadora',                   'PRO/DES/01',  'LAMINADO, SECADO Y CORTE'),

  -- ── ENCARTUCHADO ─────────────────────────────────────────
  -- COR tomado por Controlador → Cortadora Regla 2: C-O-R-T-A-D-O-R-A (9 ch, pos 4=A) → CAA
  ('Cortadora de tiras',                'PRO/CAA/01',  'ENCARTUCHADO'),
  ('Ensamblador LFIA',                  'PRO/ENS/01',  'ENCARTUCHADO'),

  -- ── ACONDICIONADO 2 ──────────────────────────────────────
  -- PRO/IMP/01 oficial existe → continúa en /02
  ('Serigrafiadora láser',              'PRO/IMP/02',  'ACONDICIONADO 2'),

  -- ── ALMACÉN DE PRODUCTO TERMINADO ────────────────────────
  -- Área distinta a ALM → REF reinicia en /01
  ('Refrigerador',                      'ALP/REF/01',  'ALMACÉN DE PRODUCTO TERMINADO'),

  -- ── CONTROL DE CALIDAD ───────────────────────────────────
  -- CEN, VER: familias nuevas en CAL → /01
  ('Centrífuga baja velocidad',         'CAL/CEN/01',  'CONTROL DE CALIDAD'),
  ('Vernier digital',                   'CAL/VER/01',  'CONTROL DE CALIDAD'),
  -- CON tomado por CAL/CON/01 (Congelador) → Conductímetro Regla 2: C-O-N-D-U-C-T-Í-M-E-T-R-O → CTO
  ('Conductímetro',                     'CAL/CTO/01',  'CONTROL DE CALIDAD'),
  -- TER tomado por CAL/TER/01 (Termohigrómetro) → Termómetro Regla 2: T-E-R-M-Ó-M-E-T-R-O → TMO
  ('Termómetro',                        'CAL/TMO/01',  'CONTROL DE CALIDAD'),

  -- ── DESARROLLO ───────────────────────────────────────────
  -- Familias ya existentes como deseables → continúan secuencia
  ('Vórtex',                            'DES/VOR/02',  'DESARROLLO'),
  ('Mini centrífuga',                   'DES/MNC/02',  'DESARROLLO'),
  ('Incubadora con agitador',           'DES/INA/02',  'DESARROLLO'),
  ('Incubadora con agitador',           'DES/INA/03',  'DESARROLLO'),
  ('Cámara de electroforesis vertical', 'DES/CEV/02',  'DESARROLLO'),
  ('Cámara de electroforesis vertical', 'DES/CEV/03',  'DESARROLLO'),
  ('Cámara de electroforesis vertical', 'DES/CEV/04',  'DESARROLLO'),
  ('Liofilizador',                      'DES/LIO/02',  'DESARROLLO'),
  ('Liofilizador',                      'DES/LIO/03',  'DESARROLLO'),
  ('Sonificador / Ultrasonicador',      'DES/SON/02',  'DESARROLLO'),
  ('Campana de extracción',             'DES/CAM/02',  'DESARROLLO'),
  -- Familias nuevas en DESARROLLO → arrancan en /01
  ('Balanza granataria',                'DES/BAL/01',  'DESARROLLO'),
  -- AGI no existe en DES → empieza en /01
  ('Agitador angular',                  'DES/AGI/01',  'DESARROLLO'),
  ('Agitador angular',                  'DES/AGI/02',  'DESARROLLO'),
  ('Agitador magnético',                'DES/AGI/03',  'DESARROLLO'),
  ('Burbuja',                           'DES/BUR/01',  'DESARROLLO'),
  -- TER tomado por oficial → Termobloque Regla 2: T-E-R-M-O-B-L-O-Q-U-E (11 ch, pos 5=B) → TBE
  ('Termobloque',                       'DES/TBE/01',  'DESARROLLO'),
  ('Analizador multiparamétrico',       'DES/ANA/01',  'DESARROLLO'),
  -- REF en DESARROLLO (área distinta a ALM/PRO) → reinicia /01
  ('Refrigerador',                      'DES/REF/01',  'DESARROLLO')
) AS t(name, serial_number, department)
WHERE NOT EXISTS (
  SELECT 1 FROM amunet_equipment x WHERE x.serial_number = t.serial_number
);

-- ============================================================
-- VERIFICACIÓN
-- ============================================================
SELECT
  COUNT(*) FILTER (WHERE is_deseable = true)              AS total_deseables,
  COUNT(*) FILTER (WHERE is_deseable = true
                   AND create_date::date = CURRENT_DATE)  AS insertados_hoy
FROM amunet_equipment;

SELECT serial_number, name, department
FROM amunet_equipment
WHERE is_deseable = true
ORDER BY serial_number;

COMMIT;
