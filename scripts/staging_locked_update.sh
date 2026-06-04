#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Uso: $0 modulo1[,modulo2,...]" >&2
  exit 2
fi

MODULES="$1"
LOCK_FILE="/tmp/odoo-deploy.lock"
WORKDIR="/opt/odoo/staging"

cd "$WORKDIR"

exec 9>"$LOCK_FILE"
echo "Esperando candado $LOCK_FILE para actualizar: $MODULES"
flock -x 9
echo "Candado adquirido: $(TZ=America/Mexico_City date '+%Y-%m-%d %H:%M:%S %Z')"

docker compose -f docker-compose.staging.yml run -T --rm --no-deps \
  -e UPDATE_MODULES="$MODULES" \
  web-staging bash -lc \
  'odoo -c /etc/odoo/odoo.conf --logfile /dev/stdout --workers 0 --max-cron-threads 0 -d Amunet_testing -u "$UPDATE_MODULES" --stop-after-init --no-http --db_host "$HOST" --db_port "$PORT" --db_user "$USER" --db_password "$PASSWORD"'

echo "Actualizacion terminada: $(TZ=America/Mexico_City date '+%Y-%m-%d %H:%M:%S %Z')"
