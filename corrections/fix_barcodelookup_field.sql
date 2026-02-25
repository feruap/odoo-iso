-- Script para corregir el campo barcodelookup_api_key en res.config.settings
-- Este script agrega la columna si no existe y asegura que el campo esté correctamente definido

-- 1. Agregar la columna barcodelookup_api_key si no existe
ALTER TABLE res_config_settings ADD COLUMN IF NOT EXISTS barcodelookup_api_key character varying;

-- 2. Agregar la columna module_stock_barcode_barcodelookup si no existe  
ALTER TABLE res_config_settings ADD COLUMN IF NOT EXISTS module_stock_barcode_barcodelookup boolean;

-- 3. Verificar que el campo exista en ir_model_fields para res.config.settings
-- Si no existe, insertarlo
INSERT INTO ir_model_fields (id, model, name, field_description, ttipo, state, required, readonly, store, index, relation_field, serialization_field_id, relation, on_delete, related_field_id, relation_table, column1, column2, compute, related, choice, column_invisible, group_expand, umodel)
SELECT 4015, 'res.config.settings', 'barcodelookup_api_key', 'API key', 'char', 'base', false, false, true, false, null, null, null, null, null, null, null, null, null, null, null, false, false, null
WHERE NOT EXISTS (SELECT 1 FROM ir_model_fields WHERE model = 'res.config.settings' AND name = 'barcodelookup_api_key');

-- 4. Verificar que el campo module_stock_barcode_barcodelookup exista
INSERT INTO ir_model_fields (id, model, name, field_description, ttipo, state, required, readonly, store, index, relation_field, serialization_field_id, relation, on_delete, related_field_id, relation_table, column1, column2, compute, related, choice, column_invisible, group_expand, umodel)
SELECT 7521, 'res.config.settings', 'module_stock_barcode_barcodelookup', 'Stock Barcode Database', 'boolean', 'base', false, false, true, false, null, null, null, null, null, null, null, null, null, null, null, false, false, null
WHERE NOT EXISTS (SELECT 1 FROM ir_model_fields WHERE model = 'res.config.settings' AND name = 'module_stock_barcode_barcodelookup');

-- 5. Actualizar el campo barcodelookup_api_key si existe pero tiene problemas
UPDATE ir_model_fields 
SET field_description = 'API key',
    ttipo = 'char',
    state = 'base'
WHERE model = 'res.config.settings' AND name = 'barcodelookup_api_key';

-- 6. Asegurar que el módulo product_barcodelookup esté marcado como instalado
UPDATE ir_module_module 
SET state = 'installed' 
WHERE name = 'product_barcodelookup' AND state != 'installed';

-- 7. Invalidar cachés de Odoo
DELETE FROM ir_config_parameter WHERE key LIKE '%cache%';
