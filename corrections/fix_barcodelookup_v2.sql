-- Script corregido para el campo barcodelookup_api_key en res.config.settings

-- 1. Ya se agregó la columna barcodelookup_api_key (del script anterior)

-- 2. Verificar que el campo exista en ir_model_fields usando la estructura correcta
-- Primero verificar si el registro ya existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM ir_model_fields WHERE model = 'res.config.settings' AND name = 'barcodelookup_api_key') THEN
        INSERT INTO ir_model_fields (id, model, name, field_description, ttype, state, required, readonly, store, index, company_dependent, group_expand, sanitize, sanitize_overridable)
        VALUES (4015, 'res.config.settings', 'barcodelookup_api_key', '{"en_US": "API key", "es_MX": "Clave API"}'::jsonb, 'char', 'base', false, false, true, false, false, false, false, false);
    END IF;
END $$;

-- 3. Actualizar el campo si existe (solo si hay problemas)
UPDATE ir_model_fields 
SET field_description = '{"en_US": "API key", "es_MX": "Clave API"}'::jsonb,
    ttype = 'char',
    state = 'base'
WHERE model = 'res.config.settings' AND name = 'barcodelookup_api_key' 
AND (ttype IS NULL OR ttype != 'char' OR state != 'base');

-- 4. Verificar que el módulo product_barcodelookup esté marcado como instalado
UPDATE ir_module_module 
SET state = 'installed' 
WHERE name = 'product_barcodelookup' AND state != 'installed';

-- 5. Forzar actualización de campos del modelo res.config.settings
UPDATE ir_model 
SET state = 'base' 
WHERE model = 'res.config.settings';

-- 6. Limpiar cache
DELETE FROM ir_config_parameter WHERE key LIKE 'ir.config.parameter%';
