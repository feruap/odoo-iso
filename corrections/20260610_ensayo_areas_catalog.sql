-- ============================================================
-- CATÁLOGO INICIAL DE ÁREAS (PCA / RCA)
-- Área: ensayo | Autor: Jorge Simarrón / Agente ensayo
-- Fecha: 2026-06-10
-- Aprobación requerida: Fernando Ruiz o Mery (desarrollo)
-- ============================================================
-- Carga las 14 áreas con sus códigos de protocolo (PCA-XX)
-- y reporte (RCA-XX). VALIDACIÓN excluida de este catálogo.
-- Producción es área padre; sus 7 subáreas la referencian.
-- ============================================================

BEGIN;

-- 1. Insertar Producción (padre, sin parent)
INSERT INTO amunet_equipment_area
  (name, protocol_code, report_code, state, parent_id, sequence,
   create_uid, write_uid, create_date, write_date)
VALUES
  ('Producción', 'PCA-01', 'RCA-01', 'vigente', NULL, 10,
   70, 70, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- 2. Insertar subáreas de Producción (referencian al padre)
DO $$
DECLARE v_prod_id INT;
BEGIN
  SELECT id INTO v_prod_id FROM amunet_equipment_area
  WHERE protocol_code = 'PCA-01' LIMIT 1;

  INSERT INTO amunet_equipment_area
    (name, protocol_code, report_code, state, parent_id, sequence,
     create_uid, write_uid, create_date, write_date)
  VALUES
    ('Soluciones',                              'PCA-01-01', 'RCA-01-01', 'vigente', v_prod_id, 11, 70,70,NOW(),NOW()),
    ('Lectura y Pretratamiento',                'PCA-01-02', 'RCA-01-02', 'vigente', v_prod_id, 12, 70,70,NOW(),NOW()),
    ('Inyección',                               'PCA-01-03', 'RCA-01-03', 'vigente', v_prod_id, 13, 70,70,NOW(),NOW()),
    ('Laminado, Secado y Corte',                'PCA-01-04', 'RCA-01-04', 'vigente', v_prod_id, 14, 70,70,NOW(),NOW()),
    ('Encartuchado',                            'PCA-01-05', 'RCA-01-05', 'vigente', v_prod_id, 15, 70,70,NOW(),NOW()),
    ('Acondicionado 1',                         'PCA-01-06', 'RCA-01-06', 'vigente', v_prod_id, 16, 70,70,NOW(),NOW()),
    ('Acondicionado 2',                         'PCA-01-07', 'RCA-01-07', 'vigente', v_prod_id, 17, 70,70,NOW(),NOW())
  ON CONFLICT DO NOTHING;
END $$;

-- 3. Insertar áreas independientes
INSERT INTO amunet_equipment_area
  (name, protocol_code, report_code, state, parent_id, sequence,
   create_uid, write_uid, create_date, write_date)
VALUES
  ('Control de Calidad',                        'PCA-02', 'RCA-02', 'vigente', NULL, 20, 70,70,NOW(),NOW()),
  ('Desarrollo',                                'PCA-03', 'RCA-03', 'vigente', NULL, 30, 70,70,NOW(),NOW()),
  ('Estabilidad',                               'PCA-04', 'RCA-04', 'vigente', NULL, 40, 70,70,NOW(),NOW()),
  ('Almacén de Materia Prima',                  'PCA-05', 'RCA-05', 'vigente', NULL, 50, 70,70,NOW(),NOW()),
  ('Almacén de Producto Terminado',             'PCA-06', 'RCA-06', 'vigente', NULL, 60, 70,70,NOW(),NOW()),
  ('Almacén Temporal de Producto Terminado',    'PCA-07', 'RCA-07', 'vigente', NULL, 70, 70,70,NOW(),NOW())
ON CONFLICT DO NOTHING;

-- Verificación
SELECT protocol_code, report_code, name, state,
       (SELECT protocol_code FROM amunet_equipment_area p WHERE p.id = a.parent_id) AS padre
FROM amunet_equipment_area a
ORDER BY sequence;

COMMIT;
