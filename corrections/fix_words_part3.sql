-- Script para corregir palabras con caracteres corruptos - Parte 3

-- Este script aplica regex replacements for JSONB fields

-- Corrige los errores del script anterior

-- Palabras con ú
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Submen\\?\\?s', 'Submenús', 'g')::jsonb WHERE arch_db::text LIKE '%Submen%s%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'aseg\\?\\?rate', 'asegúrate', 'g')::jsonb WHERE arch_db::text LIKE '%aseg%rate%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'M\\?\\?n', 'Mún', 'g')::jsonb WHERE arch_db::text LIKE '%M%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'N\\?\\?mero', 'Número', 'g')::jsonb WHERE arch_db::text LIKE '%N%mero%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'n\\?\\?mero', 'número', 'g')::jsonb WHERE arch_db::text LIKE '%n%mero%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'ning\\?\\?n', 'ningún', 'g')::jsonb WHERE arch_db::text LIKE '%ning%n%';

-- Palabras con ñ
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'peque\\?\\?as', 'pequeñas', 'g')::jsonb WHERE arch_db::text LIKE '%peque%as%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'dise\\?\\?o', 'diseño', 'g')::jsonb WHERE arch_db::text LIKE '%dise%o%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Dise\\?\\?o', 'Diseño', 'g')::jsonb WHERE arch_db::text LIKE '%Dise%o%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'contrase\\?\\?as', 'contraseñas', 'g')::jsonb WHERE arch_db::text LIKE '%contrase%as%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Contrase\\?\\?as', 'Contraseñas', 'g')::jsonb WHERE arch_db::text LIKE '%Contrase%as%';

-- Verificar resultados
SELECT COUNT(*) as corruptos_restantes FROM ir_ui_view WHERE arch_db::text ~ E'\\?\\?';
