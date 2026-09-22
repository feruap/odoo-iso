#!/bin/bash
# Blindaje de staging despues de clonar produccion.
#
# Al clonar, staging hereda las credenciales e integraciones de produccion y
# empieza a hablar con el mundo real: publica en la tienda, manda correos a
# personas y escribe en Nextcloud. Este script corta esas salidas.
#
# CORRER SIEMPRE CON ODOO STAGING APAGADO. Si el contenedor arranca antes,
# los crons disparan solos y ya no hay vuelta atras.
set -e
DB="${1:-Amunet_testing}"
C="odoo-staging-db"

if docker ps --format '{{.Names}}' | grep -q '^odoo-staging$'; then
  echo "ERROR: odoo-staging esta corriendo. Apagalo primero:"
  echo "  docker stop odoo-staging"
  exit 1
fi

echo "=== Blindando $DB ==="
docker exec -i "$C" psql -U odoo -d "$DB" <<'SQL'
-- 1. Correo: vaciar la cola heredada y apagar el servidor saliente.
--    Produccion suele traer decenas de correos pendientes; sin esto, staging
--    se los manda a personas reales, duplicados.
UPDATE mail_mail SET state='cancel' WHERE state IN ('outgoing','exception');
UPDATE ir_mail_server SET active=false;

-- 2. Tienda: quitar la llave de escritura del puente y el permiso de publicar.
--    La lectura (consumer_key) se conserva: sirve para probar y no escribe.
UPDATE amunet_woo_backend SET bridge_secret=NULL, allow_manual_publish=false;

-- 3. Apagar los crons que hablan hacia afuera.
UPDATE ir_cron SET active=false WHERE id IN (
  SELECT c.id FROM ir_cron c JOIN ir_act_server s ON s.id=c.ir_actions_server_id
  WHERE s.name->>'en_US' ILIKE ANY (ARRAY[
    '%tienda%','%woo%','%telegram%','%correo%','%mail%',
    '%aviso%','%recordatorio%','%pago%','%nextcloud%','%manual%'])
);

-- 4. Nextcloud: borrar credenciales heredadas (staging no debe escribir ahi).
DELETE FROM ir_config_parameter WHERE key LIKE 'nextcloud.%';

-- 5. Dejar marca visible de que esto NO es produccion.
INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date)
VALUES ('amunet.entorno', 'STAGING (clon de produccion) - integraciones desactivadas', 1, 1, NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value, write_date=NOW();
SQL

echo
echo "=== Verificacion ==="
docker exec "$C" psql -U odoo -d "$DB" -c "
SELECT
  (SELECT count(*) FROM mail_mail WHERE state IN ('outgoing','exception')) AS correos_en_cola,
  (SELECT count(*) FROM ir_mail_server WHERE active)                       AS smtp_activos,
  (SELECT count(*) FROM amunet_woo_backend WHERE bridge_secret IS NOT NULL) AS con_llave_tienda,
  (SELECT count(*) FROM ir_config_parameter WHERE key LIKE 'nextcloud.%')  AS credenciales_nextcloud;"
echo "Todo debe estar en CERO. Si no, revisar antes de levantar staging."
echo
echo "Ahora si: docker start odoo-staging"
