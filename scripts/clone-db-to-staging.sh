#!/bin/bash
# clone-db-to-staging.sh - Clona bases de datos de produccion a staging
set -e
PROD_CONTAINER="odoo-production-db"
STAGING_CONTAINER="odoo-staging-db"
PROD_DATA_VOL="production_odoo-production-data"
STAGING_DATA_VOL="staging_odoo-staging-data"

clone_db() {
  local DB_NAME="$1"
  local BACKUP_FILE="/tmp/backup_${DB_NAME}.dump"
  local CONTAINER_BACKUP="/tmp/restore_${DB_NAME}.dump"

  echo "--- Clonando BD: $DB_NAME ---"
  docker exec "$PROD_CONTAINER" pg_dump -F custom --no-owner --no-privileges -U odoo "$DB_NAME" > "$BACKUP_FILE"
  docker exec "$STAGING_CONTAINER" psql -U odoo -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" postgres
  docker exec "$STAGING_CONTAINER" psql -U odoo -c "DROP DATABASE IF EXISTS \"$DB_NAME\" WITH (FORCE);" postgres
  docker exec "$STAGING_CONTAINER" psql -U odoo -c "CREATE DATABASE \"$DB_NAME\";" postgres
  docker cp "$BACKUP_FILE" "${STAGING_CONTAINER}:${CONTAINER_BACKUP}"
  docker exec "$STAGING_CONTAINER" pg_restore -U odoo -d "$DB_NAME" --no-owner --no-privileges "$CONTAINER_BACKUP" || true
  docker exec "$STAGING_CONTAINER" rm -f "$CONTAINER_BACKUP"
  rm -f "$BACKUP_FILE"
  echo "--- BD $DB_NAME restaurada ---"
}

echo "=== Clonando produccion -> staging ==="
echo "[1/4] Deteniendo Odoo staging..."
docker stop odoo-staging

echo "[2/4] Clonando bases de datos..."
clone_db "amunet_prod"
clone_db "Amunet_testing"

echo "[3/4] Copiando filestores..."
docker run --rm -v "${PROD_DATA_VOL}:/prod:ro" -v "${STAGING_DATA_VOL}:/staging" alpine sh -c \
  "rm -rf /staging/filestore && mkdir -p /staging/filestore && \
   cp -r /prod/filestore/amunet_prod /staging/filestore/amunet_prod && \
   cp -r /prod/filestore/Amunet_testing /staging/filestore/Amunet_testing"

echo "[3.5/4] Limpiando cache de assets en staging (Amunet_testing)..."
docker exec "$STAGING_CONTAINER" psql -U odoo -d "Amunet_testing" -c \
  "DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%';" || true

echo "[4/4] Reiniciando Odoo staging..."
docker start odoo-staging
echo "=== Listo! staging.fc.amunet.com.mx tiene datos frescos ==="

