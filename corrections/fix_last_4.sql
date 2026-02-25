-- Corregir los últimos 4 registros con caracteres corruptos
UPDATE product_template SET name = '{"en_US": "Prueba rápida de PSA (antígeno prostático específico) semicuantitativa", "es_MX": "Prueba rápida de PSA (antígeno prostático específico) semicuantitativa"}'::jsonb WHERE id = 1324;
UPDATE product_template SET name = '{"en_US": "Prueba rápida de Antígeno de Streptococcus pneumoniae", "es_MX": "Prueba rápida de Antígeno de Streptococcus pneumoniae"}'::jsonb WHERE id = 1332;
UPDATE product_template SET name = '{"en_US": "Prueba rápida de Péptidos Natriuréticos (NT-proBNP)", "es_MX": "Prueba rápida de Péptidos Natriuréticos (NT-proBNP)"}'::jsonb WHERE id = 1319;
UPDATE product_template SET name = '{"en_US": "Prueba rápida de Antígeno de Salmonella typhi", "es_MX": "Prueba rápida de Antígeno de Salmonella typhi"}'::jsonb WHERE id = 1329;

-- Verificar
SELECT COUNT(*) as remaining FROM product_template WHERE name::text ~ E'\\?\\?';
