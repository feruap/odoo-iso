#!/bin/bash
# clone-db-to-staging.sh - Copia exacta de produccion (amunet_prod) a staging (Amunet_testing)
set -e
PROD_CONTAINER="odoo-production-db"
STAGING_CONTAINER="odoo-staging-db"
PROD_DB="amunet_prod"
STAGING_DB="Amunet_testing"
PROD_DATA_VOL="production_odoo-production-data"
STAGING_DATA_VOL="staging_odoo-staging-data"
BACKUP_FILE="/tmp/backup_amunet_prod.dump"
CONTAINER_BACKUP="/tmp/restore_prod.dump"

echo "=== Clonando produccion (amunet_prod) -> staging (Amunet_testing) ==="

echo "[1/4] Deteniendo Odoo staging..."
docker stop odoo-staging

echo "[2/4] Dump de amunet_prod..."
docker exec "$PROD_CONTAINER" pg_dump -F custom --no-owner --no-privileges -U odoo "$PROD_DB" > "$BACKUP_FILE"

echo "[3/4] Restaurando como $STAGING_DB en staging..."
docker exec "$STAGING_CONTAINER" psql -U odoo -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${STAGING_DB}' AND pid <> pg_backend_pid();" postgres
docker exec "$STAGING_CONTAINER" psql -U odoo -c "DROP DATABASE IF EXISTS \"$STAGING_DB\" WITH (FORCE);" postgres
docker exec "$STAGING_CONTAINER" psql -U odoo -c "CREATE DATABASE \"$STAGING_DB\";" postgres
docker cp "$BACKUP_FILE" "${STAGING_CONTAINER}:${CONTAINER_BACKUP}"
docker exec "$STAGING_CONTAINER" pg_restore -U odoo -d "$STAGING_DB" --no-owner --no-privileges "$CONTAINER_BACKUP" || true
docker exec "$STAGING_CONTAINER" rm -f "$CONTAINER_BACKUP"
rm -f "$BACKUP_FILE"

echo "[3.5/4] Copiando filestore y corrigiendo permisos..."
docker run --rm -v "${PROD_DATA_VOL}:/prod:ro" -v "${STAGING_DATA_VOL}:/staging" alpine sh -c \
  "rm -rf /staging/filestore/${STAGING_DB} && mkdir -p /staging/filestore && \
   cp -r /prod/filestore/${PROD_DB} /staging/filestore/${STAGING_DB} && \
   chown -R 100:101 /staging/filestore"

echo "[4/4] Limpiando cache de assets y reiniciando..."
docker exec "$STAGING_CONTAINER" psql -U odoo -d "$STAGING_DB" -c "DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%';" || true
docker start odoo-staging
echo "=== Listo! staging.fc.amunet.com.mx es copia exacta de produccion ==="
