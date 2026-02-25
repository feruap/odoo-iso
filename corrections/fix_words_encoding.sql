-- Script para corregir palabras específicas con caracteres corruptos
-- Basado en análisis de la base de datos

-- ============================================
-- PALABRAS COMUNES CON ACENTOS
-- ============================================

-- Palabras con ó
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'pron\\?\\?stico', 'pronóstico', 'g')::jsonb WHERE arch_db::text LIKE '%pron%stico%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Pr\\?\\?ximos', 'Próximos', 'g')::jsonb WHERE arch_db::text LIKE '%Pr%ximos%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'pr\\?\\?ximas', 'próximas', 'g')::jsonb WHERE arch_db::text LIKE '%pr%ximas%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'C\\?\\?digo', 'Código', 'g')::jsonb WHERE arch_db::text LIKE '%C%digo%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'c\\?\\?digo', 'código', 'g')::jsonb WHERE arch_db::text LIKE '%c%digo%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Electr\\?\\?nica', 'Electrónica', 'g')::jsonb WHERE arch_db::text LIKE '%Electr%nica%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'electr\\?\\?nica', 'electrónica', 'g')::jsonb WHERE arch_db::text LIKE '%electr%nica%';

-- Palabras con ú
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'M\\?\\?ltiples', 'Múltiples', 'g')::jsonb WHERE arch_db::text LIKE '%M%ltiples%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'm\\?\\?ltiples', 'múltiples', 'g')::jsonb WHERE arch_db::text LIKE '%m%ltiples%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'b\\?\\?squeda', 'búsqueda', 'g')::jsonb WHERE arch_db::text LIKE '%b%squeda%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'B\\?\\?squeda', 'Búsqueda', 'g')::jsonb WHERE arch_db::text LIKE '%B%squeda%';

-- Palabras con é
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Ingl\\?\\?s', 'Inglés', 'g')::jsonb WHERE arch_db::text LIKE '%Ingl%s%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'D\\?\\?bito', 'Débito', 'g')::jsonb WHERE arch_db::text LIKE '%D%bito%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'd\\?\\?bito', 'débito', 'g')::jsonb WHERE arch_db::text LIKE '%d%bito%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'T\\?\\?cnico', 'Técnico', 'g')::jsonb WHERE arch_db::text LIKE '%T%cnico%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E't\\?\\?cnico', 'técnico', 'g')::jsonb WHERE arch_db::text LIKE '%t%cnico%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E't\\?\\?cnicos', 'técnicos', 'g')::jsonb WHERE arch_db::text LIKE '%t%cnicos%';

-- Palabras con í
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'espec\\?\\?fica', 'específica', 'g')::jsonb WHERE arch_db::text LIKE '%espec%fica%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Espe\\?\\?fica', 'Específica', 'g')::jsonb WHERE arch_db::text LIKE '%Espe%fica%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'vac\\?\\?as', 'vacías', 'g')::jsonb WHERE arch_db::text LIKE '%vac%as%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'v\\?\\?as', 'vías', 'g')::jsonb WHERE arch_db::text LIKE '%v%as%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'v\\?\\?lida', 'válida', 'g')::jsonb WHERE arch_db::text LIKE '%v%lida%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Anal\\?\\?tica', 'Analítica', 'g')::jsonb WHERE arch_db::text LIKE '%Anal%tica%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'anal\\?\\?tica', 'analítica', 'g')::jsonb WHERE arch_db::text LIKE '%anal%tica%';

-- Palabras con á
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'num\\?\\?ricos', 'numéricos', 'g')::jsonb WHERE arch_db::text LIKE '%num%ricos%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'm\\?\\?nima', 'mínima', 'g')::jsonb WHERE arch_db::text LIKE '%m%nima%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'r\\?\\?pido', 'rápido', 'g')::jsonb WHERE arch_db::text LIKE '%r%pido%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Estad\\?\\?sticas', 'Estadísticas', 'g')::jsonb WHERE arch_db::text LIKE '%Estad%sticas%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'estad\\?\\?sticas', 'estadísticas', 'g')::jsonb WHERE arch_db::text LIKE '%estad%sticas%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'c\\?\\?lculo', 'cálculo', 'g')::jsonb WHERE arch_db::text LIKE '%c%lculo%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'a\\?\\?os', 'años', 'g')::jsonb WHERE arch_db::text LIKE '%a%os%';

-- Palabras con verbos
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'tomar\\?\\?n', 'tomarán', 'g')::jsonb WHERE arch_db::text LIKE '%tomar%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'generar\\?\\?n', 'generarán', 'g')::jsonb WHERE arch_db::text LIKE '%generar%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'omitir\\?\\?n', 'omitirán', 'g')::jsonb WHERE arch_db::text LIKE '%omitir%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'podr\\?\\?a', 'podría', 'g')::jsonb WHERE arch_db::text LIKE '%podr%a%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'd\\?\\?nde', 'dónde', 'g')::jsonb WHERE arch_db::text LIKE '%d%nde%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'atr\\?\\?s', 'atrás', 'g')::jsonb WHERE arch_db::text LIKE '%atr%s%';

-- Automatizaciones
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Automat\\?\\?celas', 'Automatícelas', 'g')::jsonb WHERE arch_db::text LIKE '%Automat%celas%';

-- ============================================
-- Verificar resultados
-- ============================================
SELECT COUNT(*) as corruptos_restantes FROM ir_ui_view WHERE arch_db::text ~ E'\\?\\?';
