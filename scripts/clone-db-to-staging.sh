#!/bin/bash
# clone-db-to-staging.sh - Clona produccion a staging
set -e
PROD_CONTAINER="odoo-production-db"
STAGING_CONTAINER="odoo-staging-db"
PROD_DB="amunet_prod"
STAGING_DB="Amunet_testing"
PROD_DATA_VOL="production_odoo-production-data"
STAGING_DATA_VOL="staging_odoo-staging-data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/tmp/prod_backup_${TIMESTAMP}.dump"
CONTAINER_BACKUP="/tmp/restore_staging.dump"

echo "=== Clonando produccion -> staging ==="
echo "[1/5] Deteniendo Odoo staging..."
docker stop odoo-staging
echo "[2/5] Backup base de datos produccion (formato binario)..."
docker exec "$PROD_CONTAINER" pg_dump -F custom --no-owner --no-privileges -U odoo "$PROD_DB" > "$BACKUP_FILE"
echo "[3/5] Restaurando en staging..."
# Terminar conexiones activas si existen antes de dropear
docker exec "$STAGING_CONTAINER" psql -U odoo -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${STAGING_DB}' AND pid <> pg_backend_pid();" postgres
docker exec "$STAGING_CONTAINER" psql -U odoo -c "DROP DATABASE IF EXISTS \"$STAGING_DB\" WITH (FORCE);" postgres
docker exec "$STAGING_CONTAINER" psql -U odoo -c "CREATE DATABASE \"$STAGING_DB\";" postgres
# Copiar dump al contenedor y restaurar con pg_restore (no tiene restricciones de backslash)
docker cp "$BACKUP_FILE" "${STAGING_CONTAINER}:${CONTAINER_BACKUP}"
docker exec "$STAGING_CONTAINER" pg_restore -U odoo -d "$STAGING_DB" --no-owner --no-privileges "$CONTAINER_BACKUP" || true
docker exec "$STAGING_CONTAINER" rm -f "$CONTAINER_BACKUP"
echo "[4/5] Copiando filestore..."
docker run --rm -v "${PROD_DATA_VOL}:/prod:ro" -v "${STAGING_DATA_VOL}:/staging" alpine sh -c "rm -rf /staging/filestore && cp -r /prod/filestore /staging/filestore && mv /staging/filestore/amunet_prod /staging/filestore/Amunet_testing"
echo "[5/5] Reiniciando Odoo staging..."
docker start odoo-staging
rm -f "$BACKUP_FILE"
echo "=== Listo! staging.fc.amunet.com.mx tiene datos frescos ==="


