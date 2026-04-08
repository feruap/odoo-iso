#!/bin/bash
# clone-db-to-staging.sh - Copia exacta de produccion a staging (ambas BDs)
set -e

PROD_CONTAINER="odoo-production-db"
STAGING_CONTAINER="odoo-staging-db"
PROD_DATA_VOL="production_odoo-production-data"
STAGING_DATA_VOL="staging_odoo-staging-data"

clone_db() {
  local SRC_DB="$1"
  local DST_DB="$2"
  local BACKUP_HOST="/tmp/clone_${SRC_DB}.dump"
  local BACKUP_CONT="/tmp/clone_${SRC_DB}.dump"

  echo ""
  echo "--- Clonando: produccion[$SRC_DB] -> staging[$DST_DB] ---"

  echo "  [dump] Exportando $SRC_DB desde produccion..."
  docker exec "$PROD_CONTAINER" pg_dump -F custom --no-owner --no-privileges \
    -U odoo -f "/tmp/dump_${SRC_DB}.dump" "$SRC_DB"
  docker cp "${PROD_CONTAINER}:/tmp/dump_${SRC_DB}.dump" "$BACKUP_HOST"
  docker exec "$PROD_CONTAINER" rm -f "/tmp/dump_${SRC_DB}.dump"
  echo "  Dump: $(du -sh $BACKUP_HOST | cut -f1)"

  echo "  [restore] Restaurando como $DST_DB en staging..."
  docker exec "$STAGING_CONTAINER" psql -U odoo postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DST_DB}' AND pid <> pg_backend_pid();" > /dev/null
  docker exec "$STAGING_CONTAINER" psql -U odoo postgres -c \
    "DROP DATABASE IF EXISTS \"${DST_DB}\" WITH (FORCE);"
  docker exec "$STAGING_CONTAINER" psql -U odoo postgres -c \
    "CREATE DATABASE \"${DST_DB}\";"
  docker cp "$BACKUP_HOST" "${STAGING_CONTAINER}:${BACKUP_CONT}"
  docker exec "$STAGING_CONTAINER" pg_restore -U odoo -d "$DST_DB" \
    --no-owner --no-privileges "$BACKUP_CONT" 2>&1 | grep -v "^pg_restore: creating" || true
  docker exec "$STAGING_CONTAINER" rm -f "$BACKUP_CONT"
  rm -f "$BACKUP_HOST"

  echo "  [verify] Conteo de tablas en $DST_DB:"
  TABLAS=$(docker exec "$STAGING_CONTAINER" psql -U odoo -d "$DST_DB" -t -c \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d ' ')
  echo "  Tablas restauradas: $TABLAS"
  if [ "$TABLAS" -lt 50 ]; then
    echo "  ERROR: Solo se restauraron $TABLAS tablas. Verificar dump de $SRC_DB."
    exit 1
  fi

  echo "  [filestore] Copiando filestore/$SRC_DB -> filestore/$DST_DB..."
  docker run --rm \
    -v "${PROD_DATA_VOL}:/prod:ro" \
    -v "${STAGING_DATA_VOL}:/staging" \
    alpine sh -c "
      rm -rf /staging/filestore/${DST_DB}
      mkdir -p /staging/filestore
      if [ -d /prod/filestore/${SRC_DB} ]; then
        cp -r /prod/filestore/${SRC_DB} /staging/filestore/${DST_DB}
        echo '  Filestore copiado correctamente'
      else
        echo '  WARN: No se encontro /prod/filestore/${SRC_DB}'
        echo '  Directorios disponibles en /prod/filestore:'
        ls /prod/filestore/ 2>/dev/null || echo '  (vacio)'
      fi
      chown -R 100:101 /staging/filestore
    "

  echo "  [assets] Limpiando cache de assets en $DST_DB..."
  docker exec "$STAGING_CONTAINER" psql -U odoo -d "$DST_DB" -c \
    "DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%';" || true

  echo "--- Listo: $DST_DB ---"
}

echo "=== INICIO: Clonacion de produccion a staging ==="

echo "[1/4] Deteniendo Odoo staging..."
docker stop odoo-staging

echo "[2/4] Clonando bases de datos..."
clone_db "amunet_prod"    "amunet_prod"
clone_db "Amunet_testing" "Amunet_testing"

echo "[3/4] Arrancando Odoo staging..."
docker start odoo-staging
echo "Esperando que Odoo este listo (max 2 min)..."
for i in $(seq 1 24); do
  if docker exec odoo-staging curl -sf http://localhost:8069/web/health > /dev/null 2>&1; then
    echo "Odoo listo despues de $((i * 5))s"
    break
  fi
  echo "  Intento $i/24, esperando 5s..."
  sleep 5
done

echo "[4/4] Actualizando modulos en ambas BDs..."
docker exec odoo-staging bash -c \
  'odoo -c /etc/odoo/odoo.conf -d amunet_prod -u all --stop-after-init --no-http --db_host $HOST --db_port $PORT --db_user $USER --db_password $PASSWORD'
docker exec odoo-staging bash -c \
  'odoo -c /etc/odoo/odoo.conf -d "Amunet_testing" -u all --stop-after-init --no-http --db_host $HOST --db_port $PORT --db_user $USER --db_password $PASSWORD'

docker compose -f /opt/odoo/staging/docker-compose.staging.yml restart web-staging
echo "=== FIN: staging.fc.amunet.com.mx es copia exacta de produccion ==="
