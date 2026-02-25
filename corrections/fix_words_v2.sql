-- Script completo para corregir palabras con caracteres corruptos
-- Los ?? representan vocales acentuadas o ñ dependiendo del contexto

-- ============================================
-- PALABRAS CON ó
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
-- PALABRAS CON é
-- ============================================
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'R\\?\\?gimen', 'Régimen', 'g')::jsonb WHERE arch_db::text LIKE '%R%gimen%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'p\\?\\?rdida', 'pérdida', 'g')::jsonb WHERE arch_db::text LIKE '%p%rdida%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'P\\?\\?rdida', 'Pérdida', 'g')::jsonb WHERE arch_db::text LIKE '%P%rdida%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Recu\\?\\?rdele', 'Recuérdele', 'g')::jsonb WHERE arch_db::text LIKE '%Recu%rdele%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'trav\\?\\?s', 'través', 'g')::jsonb WHERE arch_db::text LIKE '%trav%s%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'm\\?\\?todo', 'método', 'g')::jsonb WHERE arch_db::text LIKE '%m%todo%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'cr\\?\\?dito', 'crédito', 'g')::jsonb WHERE arch_db::text LIKE '%cr%dito%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'cr\\?\\?ditos', 'créditos', 'g')::jsonb WHERE arch_db::text LIKE '%cr%ditos%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'm\\?\\?tricas', 'métricas', 'g')::jsonb WHERE arch_db::text LIKE '%m%tricas%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Con\\?\\?ctese', 'Conéctese', 'g')::jsonb WHERE arch_db::text LIKE '%Con%ctese%';

-- ============================================
-- PALABRAS CON í
-- ============================================
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'env\\?\\?anos', 'envíanos', 'g')::jsonb WHERE arch_db::text LIKE '%env%anos%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'art\\?\\?culos', 'artículos', 'g')::jsonb WHERE arch_db::text LIKE '%art%culos%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'ra\\?\\?z', 'raíz', 'g')::jsonb WHERE arch_db::text LIKE '%ra%z%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E't\\?\\?pico', 'típico', 'g')::jsonb WHERE arch_db::text LIKE '%t%pico%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'D\\?\\?a', 'Día', 'g')::jsonb WHERE arch_db::text LIKE '%D%a%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'ser\\?\\?a', 'sería', 'g')::jsonb WHERE arch_db::text LIKE '%ser%a%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'categor\\?\\?a', 'categoría', 'g')::jsonb WHERE arch_db::text LIKE '%categor%a%';

-- ============================================
-- PALABRAS CON á
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
-- PALABRAS CON ú
-- ============================================
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Submen\\?\\?s', 'Submenús', 'g')::jsonb WHERE arch_db::text LIKE '%Submen%s%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'aseg\\?\\?rate', 'asegúrate', 'g')::jsonb WHERE arch_db::text LIKE '%aseg%rate%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'M\\?\\?n', 'Mún', 'g')::jsonb WHERE arch_db::text LIKE '%M%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'N\\?\\?mero', 'Número', 'g')::jsonb WHERE arch_db::text LIKE '%N%mero%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'ning\\?\\?n', 'ningún', 'g')::jsonb WHERE arch_db::text LIKE '%ning%n%';

-- ============================================
-- PALABRAS CON ñ
-- ============================================
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'peque\\?\\?as', 'pequeñas', 'g')::jsonb WHERE arch_db::text LIKE '%peque%as%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'dise\\?\\?o', 'diseño', 'g')::jsonb WHERE arch_db::text LIKE '%dise%o%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'contrase\\?\\?as', 'contraseñas', 'g')::jsonb WHERE arch_db::text LIKE '%contrase%as%';

-- ============================================
-- Verificar resultados
-- ============================================
SELECT COUNT(*) as corruptos_restantes FROM ir_ui_view WHERE arch_db::text ~ E'\\?\\?';
