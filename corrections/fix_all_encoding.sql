-- Script para corregir caracteres corruptos en todas las tablas de Odoo
-- Los ?? representan acentos que se corrompieron durante la migración

-- Función para aplicar correcciones a un campo JSONB
-- Patrones comunes de corrupción:
-- ?? → ó (ción, rápida, solución)
-- ?? → á (rápida, específxico)
-- ?? → í (división, específico)
-- ?? → ú (úrico, búscador)
-- ?? → é (época, bóveda)
-- ├│ → ó (codificación UTF-8 mal interpretada)

-- ============================================
-- 1. PRODUCT_TEMPLATE - Descripciones
-- ============================================
UPDATE product_template SET 
    description = regexp_replace(description::text, E'ci\\?\\?n', 'ción', 'g')::jsonb
WHERE description::text LIKE '%ci%n%';

UPDATE product_template SET 
    description = regexp_replace(description::text, E'r\\?\\?pida', 'rápida', 'g')::jsonb
WHERE description::text LIKE '%r%pida%';

UPDATE product_template SET 
    description = regexp_replace(description::text, E'soluci\\?\\?n', 'solución', 'g')::jsonb
WHERE description::text LIKE '%soluci%n%';

UPDATE product_template SET 
    description = regexp_replace(description::text, E'informaci\\?\\?n', 'información', 'g')::jsonb
WHERE description::text LIKE '%informaci%n%';

UPDATE product_template SET 
    description = regexp_replace(description::text, E'\\?\\?m', 'μm', 'g')::jsonb
WHERE description::text LIKE '%m%';

UPDATE product_template SET 
    description = regexp_replace(description::text, E'\\?\\?cido', 'Ácido', 'g')::jsonb
WHERE description::text LIKE '%cido%';

UPDATE product_template SET 
    description = regexp_replace(description::text, E'\\?\\?xido', 'óxido', 'g')::jsonb
WHERE description::text LIKE '%xido%';

-- ============================================
-- 2. RES_PARTNER - Nombres
-- ============================================
UPDATE res_partner SET 
    name = regexp_replace(name::text, E'\\?\\?n', 'ón', 'g')::jsonb
WHERE name::text LIKE '%n%' AND name::text LIKE '%\\?\\?%';

UPDATE res_partner SET 
    name = regexp_replace(name::text, E'ci\\?\\?n', 'ción', 'g')::jsonb
WHERE name::text LIKE '%ci%n%';

UPDATE res_partner SET 
    name = regexp_replace(name::text, E'\\?\\?n', 'ión', 'g')::jsonb
WHERE name::text LIKE '%\\?\\?n%';

-- ============================================
-- 3. STOCK_LOCATION - Nombres de ubicaciones
-- ============================================
UPDATE stock_location SET 
    name = regexp_replace(name::text, E'ci\\?\\?n', 'ción', 'g')::jsonb
WHERE name::text LIKE '%ci%n%';

UPDATE stock_location SET 
    name = regexp_replace(name::text, E'\\?\\?n', 'ón', 'g')::jsonb
WHERE name::text LIKE '%\\?\\?n%';

-- ============================================
-- 4. IR_UI_VIEW - Vistas del sistema
-- ============================================
-- Corregir el patrón ├│ que es UTF-8 mal interpretado
UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'├│', 'ó', 'g')::jsonb
WHERE arch_db::text LIKE '%├│%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'\\?\\?n', 'ón', 'g')::jsonb
WHERE arch_db::text LIKE '%\\?\\?n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'\\?\\?n', 'ión', 'g')::jsonb
WHERE arch_db::text LIKE '%\\?\\?n%';

-- ============================================
-- 5. AMUNET_QUALITY - Tablas personalizadas
-- ============================================
-- Parámetros de calidad
UPDATE amunet_quality_parameter SET 
    name = regexp_replace(name::text, E'ci\\?\\?n', 'ción', 'g')::jsonb
WHERE name::text LIKE '%ci%n%';

UPDATE amunet_quality_parameter SET 
    name = regexp_replace(name::text, E'\\?\\?n', 'ón', 'g')::jsonb
WHERE name::text LIKE '%\\?\\?n%';

-- Checks de calidad
UPDATE amunet_quality_check SET 
    notes = regexp_replace(notes::text, E'ci\\?\\?n', 'ción', 'g')::jsonb
WHERE notes IS NOT NULL AND notes::text LIKE '%ci%n%';

-- ============================================
-- 6. Verificar resultados
-- ============================================
SELECT 'product_template.name' as campo, COUNT(*) as corruptos FROM product_template WHERE name::text ~ E'\\?\\?'
UNION ALL
SELECT 'product_template.description', COUNT(*) FROM product_template WHERE description::text ~ E'\\?\\?'
UNION ALL
SELECT 'res_partner.name', COUNT(*) FROM res_partner WHERE name::text ~ E'\\?\\?'
UNION ALL
SELECT 'stock_location.name', COUNT(*) FROM stock_location WHERE name::text ~ E'\\?\\?'
UNION ALL
SELECT 'ir_ui_view.arch_db', COUNT(*) FROM ir_ui_view WHERE arch_db::text ~ E'\\?\\?|├│';
