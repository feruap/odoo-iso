-- Script para forzar la reinstalación del módulo product_barcodelookup

-- 1. Primero, marcar el módulo para desinstalar
UPDATE ir_module_module 
SET state = 'to remove' 
WHERE name = 'product_barcodelookup';

-- 2. También desinstalar módulos relacionados que dependen de él
UPDATE ir_module_module 
SET state = 'to remove' 
WHERE name IN ('stock_barcode_barcodelookup', 'website_product_barcodelookup', 'pos_barcodelookup');

-- 3. Limpiar la caché de Odoo
DELETE FROM ir_config_parameter WHERE key LIKE 'web.%';
DELETE FROM ir_config_parameter WHERE key LIKE 'cache.%';

-- 4. Forzar actualización de la registry de modelos
DELETE FROM ir_model_relation WHERE model IN ('res.config.settings');

-- Nota: Después de ejecutar esto,你需要 ejecutar:
-- docker-compose restart web
-- Luego en Odoo: Aplicaciones > Actualizar lista de aplicaciones
-- Y buscar "Product Barcode Lookup" y reinstallarlo
