-- Script comprehensivo para corregir TODOS los caracteres corruptos en la base de datos
-- Este script se ejecut en múltiples passes for efficiency

-- Pass 1: Corregir palabras comunes con ó
-- Pass 2: Corregir palabras comunes con í
-- Pass 3: Corregir palabras comunes con ú
-- Pass 4: Corregir palabras comunes con á
-- Pass 5: Corregir palabras comunes con é
-- Pass 6: Corregir palabras comunes con ñ
-- Pass 7: Corregir palabras comunes con otros

-- Pass 8: Reiniciar Odoo

-- Pass 9: Verificar resultados

-- ============================================
-- PASS 1: Palabras con ó
-- ============================================
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Expresi\\?\\?n', 'Expresión', 'g')::jsonb WHERE arch_db::text LIKE '%Expresi%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'precisi\\?\\?n', 'precisión', 'g')::jsonb WHERE arch_db::text LIKE '%precisi%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Regi\\?\\?n', 'Región', 'g')::jsonb WHERE arch_db::text LIKE '%Regi%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Prop\\?\\?n', 'Propón', 'g')::jsonb WHERE arch_db::text LIKE '%Prop%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'M\\?\\?dulo', 'Módulo', 'g')::jsonb WHERE arch_db::text LIKE '%M%dulo%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'sesi\\?\\?n', 'sesión', 'g')::jsonb WHERE arch_db::text LIKE '%sesi%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Sesi\\?\\?n', 'Sesión', 'g')::jsonb WHERE arch_db::text LIKE '%Sesi%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'N\\?\\?mina', 'Nómina', 'g')::jsonb WHERE arch_db::text LIKE '%N%mina%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'telef\\?\\?nicos', 'telefónicos', 'g')::jsonb WHERE arch_db::text LIKE '%telef%nicos%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'C\\?\\?mo', 'Cómo', 'g')::jsonb WHERE arch_db::text LIKE '%C%mo%';

-- ============================================
-- PASS 2: Palabras con é
-- ============================================
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'R\\?\\?gimen', 'Régimen', 'g')::jsonb WHERE arch_db::text LIKE '%R%gimen%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'p\\?\\?rdida', 'pérdida', 'g')::jsonb WHERE arch_db::text LIKE '%p%rdida%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'P\\?\\?rdida', 'Pérdida', 'g')::jsonb WHERE arch_db::text LIKE '%P%rdida%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Recu\\?\\?rdele', 'Recuérdele', 'g')::jsonb WHERE arch_db::text LIKE '%Recu%rdele%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'trav\\?\\?s', 'través', 'g')::jsonb WHERE arch_db::text LIKE '%trav%s%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'm\\?\\?todo', 'método', 'g')::jsonb WHERE arch_db::text LIKE '%m%todo%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'cr\\?\\?dito', 'crédito', 'g')::jsonb WHERE arch_db::text LIKE '%cr%dito%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'cr\\?\\?ditos', 'créditos', 'g')::jsonb WHERE arch_db::text LIKE '%cr%ditos%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Con\\?\\?ctese', 'Conéctese', 'g')::jsonb WHERE arch_db::text LIKE '%Con%ctese%';

-- ============================================
-- PASS 3: Palabras con í
-- ============================================
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'env\\?\\?anos', 'envíanos', 'g')::jsonb WHERE arch_db::text LIKE '%env%anos%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'art\\?\\?culos', 'artículos', 'g')::jsonb WHERE arch_db::text LIKE '%art%culos%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'ra\\?\\?z', 'raíz', 'g')::jsonb WHERE arch_db::text LIKE '%ra%z%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E't\\?\\?pico', 'típico', 'g')::jsonb WHERE arch_db::text LIKE '%t%pico%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'D\\?\\?a', 'Día', 'g')::jsonb WHERE arch_db::text LIKE '%D%a%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'ser\\?\\?a', 'sería', 'g')::jsonb WHERE arch_db::text LIKE '%ser%a%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'categor\\?\\?a', 'categoría', 'g')::jsonb WHERE arch_db::text LIKE '%categor%a%';

-- ============================================
-- PASS 4: Palabras con á
-- ============================================
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'instalar\\?\\?n', 'instalarán', 'g')::jsonb WHERE arch_db::text LIKE '%instalar%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'cu\\?\\?ndo', 'cuándo', 'g')::jsonb WHERE arch_db::text LIKE '%cu%ndo%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'detr\\?\\?s', 'detrás', 'g')::jsonb WHERE arch_db::text LIKE '%detr%s%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'est\\?\\?ndar', 'estándar', 'g')::jsonb WHERE arch_db::text LIKE '%est%ndar%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'M\\?\\?ximo', 'Máximo', 'g')::jsonb WHERE arch_db::text LIKE '%M%ximo%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'procesar\\?\\?s', 'procesarás', 'g')::jsonb WHERE arch_db::text LIKE '%procesar%s%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'p\\?\\?gina', 'página', 'g')::jsonb WHERE arch_db::text LIKE '%p%gina%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'crear\\?\\?n', 'crearán', 'g')::jsonb WHERE arch_db::text LIKE '%crear%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'autom\\?\\?tico', 'automático', 'g')::jsonb WHERE arch_db::text LIKE '%autom%tico%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Gr\\?\\?fico', 'Gráfico', 'g')::jsonb WHERE arch_db::text LIKE '%Gr%fico%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Par\\?\\?metros', 'Parámetros', 'g')::jsonb WHERE arch_db::text LIKE '%Par%metros%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'V\\?\\?lido', 'Válido', 'g')::jsonb WHERE arch_db::text LIKE '%V%lido%';

-- ============================================
-- PASS 5: Palabras con ú
-- ============================================
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Submen\\?\\?s', 'Submenús', 'g')::jsonb WHERE arch_db::text LIKE '%Submen%s%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'aseg\\?\\?rate', 'asegúrate', 'g')::jsonb WHERE arch_db::text LIKE '%aseg%rate%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'M\\?\\?n', 'Mún', 'g')::jsonb WHERE arch_db::text LIKE '%M%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'N\\?\\?mero', 'Número', 'g')::jsonb WHERE arch_db::text LIKE '%N%mero%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'n\\?\\?mero', 'número', 'g')::jsonb WHERE arch_db::text LIKE '%n%mero%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'ning\\?\\?n', 'ningún', 'g')::jsonb WHERE arch_db::text LIKE '%ning%n%';

-- ============================================
-- PASS 6: Palabras con ñ
-- ============================================
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'peque\\?\\?as', 'pequeñas', 'g')::jsonb WHERE arch_db::text LIKE '%peque%as%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'dise\\?\\?o', 'diseño', 'g')::jsonb WHERE arch_db::text LIKE '%dise%o%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Dise\\?\\?o', 'Diseño', 'g')::jsonb WHERE arch_db::text LIKE '%Dise%o%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'contrase\\?\\?as', 'contraseñas', 'g')::jsonb WHERE arch_db::text LIKE '%contrase%as%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Contrase\\?\\?as', 'Contraseñas', 'g')::jsonb WHERE arch_db::text LIKE '%Contrase%as%';

-- ============================================
-- PASS 7: Palabras com others
-- ============================================
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Automat\\?\\?celas', 'Automatícelas', 'g')::jsonb WHERE arch_db::text LIKE '%Automat%celas%';

-- ============================================
-- PASS 8: Reiniciar Odoo
-- ============================================
-- Reiniciar to container
docker restart odoo-docker-web-1;

