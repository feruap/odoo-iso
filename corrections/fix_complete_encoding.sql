-- Script completo para corregir caracteres corruptos en Odoo 19
-- Maneja tanto campos JSONB como VARCHAR

-- ============================================
-- 1. IR_UI_VIEW - Vistas del sistema (JSONB)
-- ============================================

-- Patrón ├│ (UTF-8 mal interpretado)
UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'├│', 'ó', 'g')::jsonb
WHERE arch_db::text LIKE '%├│%';

-- Patrón ?? → ó (ción, solución, etc.)
UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'ci\\?\\?n', 'ción', 'g')::jsonb
WHERE arch_db::text LIKE '%ci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'soluci\\?\\?n', 'solución', 'g')::jsonb
WHERE arch_db::text LIKE '%soluci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'informaci\\?\\?n', 'información', 'g')::jsonb
WHERE arch_db::text LIKE '%informaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'configuraci\\?\\?n', 'configuración', 'g')::jsonb
WHERE arch_db::text LIKE '%configuraci%n%';

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

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'acci\\?\\?n', 'acción', 'g')::jsonb
WHERE arch_db::text LIKE '%acci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'aplicaci\\?\\?n', 'aplicación', 'g')::jsonb
WHERE arch_db::text LIKE '%aplicaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'relaci\\?\\?n', 'relación', 'g')::jsonb
WHERE arch_db::text LIKE '%relaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'conexi\\?\\?n', 'conexión', 'g')::jsonb
WHERE arch_db::text LIKE '%conexi%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'selecci\\?\\?n', 'selección', 'g')::jsonb
WHERE arch_db::text LIKE '%selecci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'direcci\\?\\?n', 'dirección', 'g')::jsonb
WHERE arch_db::text LIKE '%direcci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'funci\\?\\?n', 'función', 'g')::jsonb
WHERE arch_db::text LIKE '%funci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'secci\\?\\?n', 'sección', 'g')::jsonb
WHERE arch_db::text LIKE '%secci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'clasificaci\\?\\?n', 'clasificación', 'g')::jsonb
WHERE arch_db::text LIKE '%clasificaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'identificaci\\?\\?n', 'identificación', 'g')::jsonb
WHERE arch_db::text LIKE '%identificaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'implementaci\\?\\?n', 'implementación', 'g')::jsonb
WHERE arch_db::text LIKE '%implementaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'generaci\\?\\?n', 'generación', 'g')::jsonb
WHERE arch_db::text LIKE '%generaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'validaci\\?\\?n', 'validación', 'g')::jsonb
WHERE arch_db::text LIKE '%validaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'evaluaci\\?\\?n', 'evaluación', 'g')::jsonb
WHERE arch_db::text LIKE '%evaluaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'presentaci\\?\\?n', 'presentación', 'g')::jsonb
WHERE arch_db::text LIKE '%presentaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'representaci\\?\\?n', 'representación', 'g')::jsonb
WHERE arch_db::text LIKE '%representaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'organizaci\\?\\?n', 'organización', 'g')::jsonb
WHERE arch_db::text LIKE '%organizaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'autorizaci\\?\\?n', 'autorización', 'g')::jsonb
WHERE arch_db::text LIKE '%autorizaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'cancelaci\\?\\?n', 'cancelación', 'g')::jsonb
WHERE arch_db::text LIKE '%cancelaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'creaci\\?\\?n', 'creación', 'g')::jsonb
WHERE arch_db::text LIKE '%creaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'modificaci\\?\\?n', 'modificación', 'g')::jsonb
WHERE arch_db::text LIKE '%modificaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'eliminaci\\?\\?n', 'eliminación', 'g')::jsonb
WHERE arch_db::text LIKE '%eliminaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'activaci\\?\\?n', 'activación', 'g')::jsonb
WHERE arch_db::text LIKE '%activaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'desactivaci\\?\\?n', 'desactivación', 'g')::jsonb
WHERE arch_db::text LIKE '%desactivaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'actualizaci\\?\\?n', 'actualización', 'g')::jsonb
WHERE arch_db::text LIKE '%actualizaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'asignaci\\?\\?n', 'asignación', 'g')::jsonb
WHERE arch_db::text LIKE '%asignaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'asociaci\\?\\?n', 'asociación', 'g')::jsonb
WHERE arch_db::text LIKE '%asociaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'comunicaci\\?\\?n', 'comunicación', 'g')::jsonb
WHERE arch_db::text LIKE '%comunicaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'documentaci\\?\\?n', 'documentación', 'g')::jsonb
WHERE arch_db::text LIKE '%documentaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'especificaci\\?\\?n', 'especificación', 'g')::jsonb
WHERE arch_db::text LIKE '%especificaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'certificaci\\?\\?n', 'certificación', 'g')::jsonb
WHERE arch_db::text LIKE '%certificaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'notificaci\\?\\?n', 'notificación', 'g')::jsonb
WHERE arch_db::text LIKE '%notificaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'verificaci\\?\\?n', 'verificación', 'g')::jsonb
WHERE arch_db::text LIKE '%verificaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'confirmaci\\?\\?n', 'confirmación', 'g')::jsonb
WHERE arch_db::text LIKE '%confirmaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'administraci\\?\\?n', 'administración', 'g')::jsonb
WHERE arch_db::text LIKE '%administraci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'instalaci\\?\\?n', 'instalación', 'g')::jsonb
WHERE arch_db::text LIKE '%instalaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'publicaci\\?\\?n', 'publicación', 'g')::jsonb
WHERE arch_db::text LIKE '%publicaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'ubicaci\\?\\?n', 'ubicación', 'g')::jsonb
WHERE arch_db::text LIKE '%ubicaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'integraci\\?\\?n', 'integración', 'g')::jsonb
WHERE arch_db::text LIKE '%integraci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'migraci\\?\\?n', 'migración', 'g')::jsonb
WHERE arch_db::text LIKE '%migraci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'importaci\\?\\?n', 'importación', 'g')::jsonb
WHERE arch_db::text LIKE '%importaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'exportaci\\?\\?n', 'exportación', 'g')::jsonb
WHERE arch_db::text LIKE '%exportaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'facturaci\\?\\?n', 'facturación', 'g')::jsonb
WHERE arch_db::text LIKE '%facturaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'cotizaci\\?\\?n', 'cotización', 'g')::jsonb
WHERE arch_db::text LIKE '%cotizaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'programaci\\?\\?n', 'programación', 'g')::jsonb
WHERE arch_db::text LIKE '%programaci%n%';

UPDATE ir_ui_view SET 
    arch_db = regexp_replace(arch_db::text, E'planificaci\\?\\?n', 'planificación', 'g')::jsonb
WHERE arch_db::text LIKE '%planificaci%n%';

-- ============================================
-- 2. RES_PARTNER - Nombres (VARCHAR)
-- ============================================
UPDATE res_partner SET name = regexp_replace(name, E'\\?\\?', 'ó', 'g') WHERE name LIKE '%??%';
UPDATE res_partner SET name = regexp_replace(name, E'ci\\?\\?n', 'ción', 'g') WHERE name LIKE '%ci%n%';
UPDATE res_partner SET name = regexp_replace(name, E'\\?\\?n', 'ión', 'g') WHERE name LIKE '%??n%';

-- ============================================
-- 3. STOCK_LOCATION - Nombres (VARCHAR)
-- ============================================
UPDATE stock_location SET name = regexp_replace(name, E'\\?\\?', 'ó', 'g') WHERE name LIKE '%??%';
UPDATE stock_location SET name = regexp_replace(name, E'ci\\?\\?n', 'ción', 'g') WHERE name LIKE '%ci%n%';
UPDATE stock_location SET name = regexp_replace(name, E'\\?\\?n', 'ión', 'g') WHERE name LIKE '%??n%';

-- ============================================
-- 4. Verificar resultados
-- ============================================
SELECT 'ir_ui_view.arch_db' as campo, COUNT(*) as corruptos FROM ir_ui_view WHERE arch_db::text ~ E'\\?\\?|├│'
UNION ALL
SELECT 'res_partner.name', COUNT(*) FROM res_partner WHERE name ~ E'\\?\\?|├│'
UNION ALL
SELECT 'stock_location.name', COUNT(*) FROM stock_location WHERE name ~ E'\\?\\?|├│';
