-- Script corregido para caracteres corruptos en Odoo19
-- Algunos campos son JSONB, otros son TEXT

-- ============================================
-- 1. IR_UI_VIEW - Vistas del sistema (JSONB)
-- ============================================
-- Corregir el patrón ├│ que es UTF-8 mal interpretado
UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'├│', 'ó', 'g')::jsonb
WHERE arch_db::text LIKE '%├│%';

-- Corregir ?? con contexto
UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'ci\\?\\?n', 'ción', 'g')::jsonb
WHERE arch_db::text LIKE '%ci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'informaci\\?\\?n', 'información', 'g')::jsonb
WHERE arch_db::text LIKE '%informaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'soluci\\?\\?n', 'solución', 'g')::jsonb
WHERE arch_db::text LIKE '%soluci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'configuraci\\?\\?n', 'configuración', 'g')::jsonb
WHERE arch_db::text LIKE '%configuraci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'acci\\?\\?n', 'acción', 'g')::jsonb
WHERE arch_db::text LIKE '%acci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'descripci\\?\\?n', 'descripción', 'g')::jsonb
WHERE arch_db::text LIKE '%descripci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'operaci\\?\\?n', 'operación', 'g')::jsonb
WHERE arch_db::text LIKE '%operaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'versi\\?\\?n', 'versión', 'g')::jsonb
WHERE arch_db::text LIKE '%versi%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'inspecci\\?\\?n', 'inspección', 'g')::jsonb
WHERE arch_db::text LIKE '%inspecci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'determinaci\\?\\?n', 'determinación', 'g')::jsonb
WHERE arch_db::text LIKE '%determinaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'revisi\\?\\?n', 'revisión', 'g')::jsonb
WHERE arch_db::text LIKE '%revisi%n%';

-- ============================================
-- 2. RES_PARTNER - Nombres (campo es VARCHAR)
-- ============================================
-- Primero veo la estructura de la tabla
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'res_partner' AND column_name = 'name';

-- ============================================
-- 3. STOCK_LOCATION - Nombres (campo es VARCHAR)
-- ============================================
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'stock_location' AND column_name = 'name';

-- ============================================
-- 4. Verificar resultados
-- ============================================
SELECT 'ir_ui_view.arch_db' as campo, COUNT(*) as corruptos FROM ir_ui_view WHERE arch_db::text ~ E'\\?\\?|├│';
