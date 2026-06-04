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
echo "Esperando candado $LOCK_FILE para rebuild/update/recreate: $MODULES"
flock -x 9
echo "Candado adquirido: $(TZ=America/Mexico_City date '+%Y-%m-%d %H:%M:%S %Z')"

docker compose -f docker-compose.staging.yml build web-staging

docker compose -f docker-compose.staging.yml run -T --rm --no-deps \
  -e UPDATE_MODULES="$MODULES" \
  web-staging bash -lc \
  'odoo -c /etc/odoo/odoo.conf --logfile /dev/stdout --workers 0 --max-cron-threads 0 -d Amunet_testing -u "$UPDATE_MODULES" --stop-after-init --no-http --db_host "$HOST" --db_port "$PORT" --db_user "$USER" --db_password "$PASSWORD"'

docker compose -f docker-compose.staging.yml up -d --force-recreate web-staging

echo "Esperando healthcheck de staging..."
for _ in $(seq 1 36); do
  status="$(docker inspect -f '{{.State.Health.Status}}' odoo-staging 2>/dev/null || echo no-container)"
  echo "health=$status"
  [ "$status" = "healthy" ] && exit 0
  sleep 5
done

echo "Staging no llego a healthy dentro del tiempo esperado." >&2
exit 1
