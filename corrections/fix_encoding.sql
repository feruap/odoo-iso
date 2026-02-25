-- Corregir caracteres corruptos en product_template
-- Los ?? representan acentos que se corrompieron

-- División
UPDATE product_template SET name = regexp_replace(name::text, E'divisi\\?\\?n', 'división', 'g')::jsonb WHERE name::text LIKE '%divisi%n%';

-- Ácido (al inicio)
UPDATE product_template SET name = regexp_replace(name::text, E'\\?\\?cido', 'Ácido', 'g')::jsonb WHERE name::text LIKE '%cido%';

-- óxido
UPDATE product_template SET name = regexp_replace(name::text, E'\\?\\?xido', 'óxido', 'g')::jsonb WHERE name::text LIKE '%xido%';

-- úrico
UPDATE product_template SET name = regexp_replace(name::text, E'\\?\\?urico', 'úrico', 'g')::jsonb WHERE name::text LIKE '%urico%';

-- Tritón
UPDATE product_template SET name = regexp_replace(name::text, E'Trit\\?\\?n', 'Tritón', 'g')::jsonb WHERE name::text LIKE '%Trit%n%';

-- órico (bórico, fosfórico)
UPDATE product_template SET name = regexp_replace(name::text, E'\\?\\?rico', 'órico', 'g')::jsonb WHERE name::text LIKE '%rico%' AND name::text LIKE '%cido%';

-- áctica
UPDATE product_template SET name = regexp_replace(name::text, E'\\?\\?ctica', 'áctica', 'g')::jsonb WHERE name::text LIKE '%ctica%';

-- Tétanos
UPDATE product_template SET name = regexp_replace(name::text, E'T\\?\\?tanos', 'Tétanos', 'g')::jsonb WHERE name::text LIKE '%T%tanos%';

-- Respiratorio
UPDATE product_template SET name = regexp_replace(name::text, E'Respirator\\?\\?o', 'Respiratorio', 'g')::jsonb WHERE name::text LIKE '%Respirator%o%';

-- Nanopartículas
UPDATE product_template SET name = regexp_replace(name::text, E'Nanopart\\?\\?culas', 'Nanopartículas', 'g')::jsonb WHERE name::text LIKE '%Nanopart%culas%';

-- antígeno
UPDATE product_template SET name = regexp_replace(name::text, E'ant\\?\\?geno', 'antígeno', 'g')::jsonb WHERE name::text LIKE '%ant%geno%';

-- Péptidos
UPDATE product_template SET name = regexp_replace(name::text, E'P\\?\\?ptidos', 'Péptidos', 'g')::jsonb WHERE name::text LIKE '%P%ptidos%';

-- prostático
UPDATE product_template SET name = regexp_replace(name::text, E'prost\\?\\?tico', 'prostático', 'g')::jsonb WHERE name::text LIKE '%prost%tico%';

-- Sífilis
UPDATE product_template SET name = regexp_replace(name::text, E'S\\?\\?filis', 'Sífilis', 'g')::jsonb WHERE name::text LIKE '%S%filis%';

-- vías
UPDATE product_template SET name = regexp_replace(name::text, E'v\\?\\?as', 'vías', 'g')::jsonb WHERE name::text LIKE '%v%as urinarias%';

-- í (palabra sola)
UPDATE product_template SET name = regexp_replace(name::text, E' \\?\\? ', ' í ', 'g')::jsonb WHERE name::text LIKE '% % %';

-- Verificar resultados
SELECT COUNT(*) as remaining_corrupt FROM product_template WHERE name::text ~ E'\\?\\?';
