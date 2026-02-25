-- Script específico para insertar el campo barcodelookup_api_key en ir_model_fields

-- Verificar si el modelo base res.config.settings existe
-- Primero obtener el model_id correcto
DO $$
DECLARE
    v_model_id integer;
    v_field_exists boolean;
BEGIN
    -- Buscar el ID del modelo res.config.settings
    SELECT id INTO v_model_id FROM ir_model WHERE model = 'res.config.settings' LIMIT 1;
    
    IF v_model_id IS NULL THEN
        RAISE NOTICE 'Modelo res.config.settings no encontrado en ir_model';
    ELSE
        RAISE NOTICE 'Modelo res.config.settings encontrado con ID: %', v_model_id;
    END IF;
    
    -- Verificar si el campo ya existe
    SELECT EXISTS(SELECT 1 FROM ir_model_fields WHERE model = 'res.config.settings' AND name = 'barcodelookup_api_key') INTO v_field_exists;
    
    IF v_field_exists THEN
        RAISE NOTICE 'El campo barcodelookup_api_key ya existe';
    ELSE
        RAISE NOTICE 'El campo NO existe, necesita ser creado';
    END IF;
END $$;

-- Insertar el campo barcodelookup_api_key si no existe
-- Necesitamos primero el model_id
INSERT INTO ir_model_fields (
    id, 
    model_id, 
    name, 
    field_description, 
    ttype, 
    state, 
    required, 
    readonly, 
    store, 
    index, 
    company_dependent, 
    group_expand, 
    sanitize, 
    sanitize_overridable,
    create_uid,
    write_uid,
    create_date,
    write_date
)
SELECT 
    4015,
    (SELECT id FROM ir_model WHERE model = 'res.config.settings' LIMIT 1),
    'barcodelookup_api_key',
    '{"en_US": "API key", "es_MX": "Clave API"}'::jsonb,
    'char',
    'base',
    false,
    false,
    true,
    false,
    false,
    false,
    false,
    false,
    1,
    1,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM ir_model_fields 
    WHERE model = 'res.config.settings' AND name = 'barcodelookup_api_key'
);

-- Verificar el resultado
SELECT name, ttype, state, field_description FROM ir_model_fields 
WHERE model = 'res.config.settings' AND name = 'barcodelookup_api_key';
