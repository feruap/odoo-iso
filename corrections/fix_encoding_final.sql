-- Script simple para corregir caracteres corruptos
-- Ejecutar en múltiples pasos

-- Paso 1: Corregir palabras con ó
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

-- Pass 2: Corregir palabras con é
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'R\\?\\?gimen', 'Régimen', 'g')::jsonb WHERE arch_db::text LIKE '%R%gimen%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'p\\?\\?rdida', 'pérdida', 'g')::jsonb WHERE arch_db::text LIKE '%p%rdida%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'P\\?\\?rdida', 'Pérdida', 'g')::jsonb WHERE arch_db::text LIKE '%P%rdida%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Recu\\?\\?rdele', 'Recuérdele', 'g')::jsonb WHERE arch_db::text LIKE '%Recu%rdeel%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'trav\\?\\?s', 'través', 'g')::jsonb WHERE arch_db::text LIKE '%trav%s%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'm\\?\\?todo', 'método', 'g')::jsonb WHERE arch_db::text LIKE '%m%todo%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'cr\\?\\?dito', 'crédito', 'g')::jsonb WHERE arch_db::text LIKE '%cr%dito%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'cr\\?\\?ditos', 'créditos', 'g')::jsonb WHERE arch_db::text LIKE '%cr%ditos%';

-- Pass 3: Corregir palabras con í
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'D\\?\\?a', 'Día', 'g')::jsonb WHERE arch_db::text LIKE '%D%a%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'ser\\?\\?a', 'sería', 'g')::jsonb WHERE arch_db::text LIKE '%ser%a%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'categor\\?\\?a', 'categoría', 'g')::jsonb WHERE arch_db::text LIKE '%categor%a%';

-- Pass 4: Corregir palabras con á
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'instalar\\?\\?n', 'instalarán', 'g')::jsonb WHERE arch_db::text LIKE '%instalar%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'cu\\?\\?ndo', 'cuándo', 'g')::jsonb WHERE arch_db::text LIKE '%cu%ndo%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'detr\\?\\?s', 'detrás', 'g')::jsonb WHERE arch_db::text LIKE '%detr%s%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'est\\?\\?ndar', 'estándar', 'g')::jsonb WHERE arch_db::text LIKE '%est%ndar%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Gr\\?\\?fico', 'Gráfico', 'g')::jsonb WHERE arch_db::text LIKE '%Gr%fico%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Par\\?\\?metros', 'Parámetros', 'g')::jsonb WHERE arch_db::text LIKE '%Par%metros%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'V\\?\\?lido', 'Válido', 'g')::jsonb WHERE arch_db::text LIKE '%V%lido%';

-- Pass 5: Corregir palabras con ú
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Submen\\?\\?s', 'Submenús', 'g')::jsonb WHERE arch_db::text LIKE '%Submen%s%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'aseg\\?\\?rate', 'asegúrate', 'g')::jsonb WHERE arch_db::text LIKE '%aseg%rate%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'M\\?\\?n', 'Mún', 'g')::jsonb WHERE arch_db::text LIKE '%M%n%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'N\\?\\?mero', 'Número', 'g')::jsonb WHERE arch_db::text LIKE '%N%mero%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'n\\?\\?mero', 'número', 'g')::jsonb WHERE arch_db::text LIKE '%n%mero%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'ning\\?\\?n', 'ningún', 'g')::jsonb WHERE arch_db::text LIKE '%ning%n%';

-- Pass 6: Corregir palabras con ñ
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'peque\\?\\?as', 'pequeñas', 'g')::jsonb WHERE arch_db::text LIKE '%peque%as%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'dise\\?\\?o', 'diseño', 'g')::jsonb WHERE arch_db::text LIKE '%dise%o%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Dise\\?\\?o', 'Diseño', 'g')::jsonb WHERE arch_db::text LIKE '%Dise%o%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'contrase\\?\\?as', 'contraseñas', 'g')::jsonb WHERE arch_db::text LIKE '%contrase%as%';
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Contrase\\?\\?as', 'Contraseñas', 'g')::jsonb WHERE arch_db::text LIKE '%Contrase%as%';

-- Pass 7: Palabras com others
UPDATE ir_ui_view SET arch_db = regexp_replace(arch_db::text, E'Automat\\?\\?celas', 'Automatícelas', 'g')::jsonb WHERE arch_db::text LIKE '%Automat%celas%';

-- Pass 8: Reiniciar Odoo
docker restart odoo-docker-web-1;

