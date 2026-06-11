-- ============================================================
-- MICROPIPETAS: limpiar nombre (quitar volumen) + marca y serial FVA
-- Área: ensayo | Autor: Jorge Simarrón / Agente ensayo
-- Fecha: 2026-06-11
-- Fuente: FVA-002 Programa 2026 de calibración-caracterización
-- ============================================================
-- QUÉ HACE:
--   1. Limpia el campo nombre: quita el rango de volumen y deja "Micropipeta"
--   2. Actualiza marca (brand) con los datos del programa FVA
--   3. Actualiza modelo (model_name) con el No. de serie del fabricante del FVA
--   Solo afecta equipos cuyo serial_number contiene /MIC/
-- ============================================================

BEGIN;

UPDATE amunet_equipment eq
SET
    name       = 'Micropipeta',
    brand      = COALESCE(t.fva_brand, eq.brand),  -- si FVA no trae marca, conserva la existente
    model_name = t.fva_serial,
    write_uid  = 70,
    write_date = NOW()
FROM (VALUES
  -- CONTROL DE CALIDAD
  ('CAL/MIC/01', NULL,          'YE243BK0013023'),
  ('CAL/MIC/02', NULL,          '50040103000865'),
  ('CAL/MIC/03', 'BIOPETTE',    '5444060419'),
  ('CAL/MIC/04', 'PIPETTE',     'PP01M40320050'),
  ('CAL/MIC/05', 'LABNET',      '544050197'),
  ('CAL/MIC/07', 'PIPETTE P',   '50040108003099'),
  ('CAL/MIC/08', 'PIPETTE P',   'P05040320043'),
  ('CAL/MIC/09', 'PIPETTE P',   'P05041128057'),
  ('CAL/MIC/10', 'PIPETTE P',   'P01M40320048'),
  -- DESARROLLO
  ('DES/MIC/01', 'ACCUMAX',     'SJ1016217'),
  ('DES/MIC/02', 'ACCUMAX',     'SJ1016235'),
  ('DES/MIC/03', 'LABNET',      '544030207'),
  ('DES/MIC/04', 'LABNET',      '544050205'),
  ('DES/MIC/05', 'LABNET PLUS', '240750656'),
  ('DES/MIC/06', 'LABNET PLUS', '240761154'),
  ('DES/MIC/07', 'PIPETTE P',   'P01M40320049'),
  ('DES/MIC/08', 'PIPETTE P',   'P05040320044'),
  ('DES/MIC/09', 'PIPETTE P',   'P05040320002'),
  ('DES/MIC/10', 'ACCUMAX',     'TK196695'),
  -- SOLUCIONES (PRODUCCIÓN)
  ('PRO/MIC/01', 'DLAB',        'YL214AK0050512'),
  ('PRO/MIC/02', NULL,          'YL214AK0045135'),
  ('PRO/MIC/03', NULL,          'YE222AX0067997'),
  ('PRO/MIC/04', 'LICHEN',      '135238'),
  ('PRO/MIC/05', 'LICHEN',      '135307'),
  ('PRO/MIC/06', 'LICHEN',      '152758'),
  ('PRO/MIC/07', NULL,          'YE223AXO138492'),
  ('PRO/MIC/08', 'LABNET',      '544030208'),
  ('PRO/MIC/09', 'PIPETTE P',   'P05040320047'),
  ('PRO/MIC/10', 'ACCUMAX',     'SJ1016245')
) AS t(serial_number, fva_brand, fva_serial)
WHERE eq.serial_number = t.serial_number;

-- Verificación
SELECT serial_number, name, brand, model_name AS serial_fabricante
FROM amunet_equipment
WHERE serial_number LIKE '%/MIC/%'
ORDER BY serial_number;

COMMIT;
