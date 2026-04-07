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
BACKUP_FILE="/tmp/prod_backup_${TIMESTAMP}.sql"

echo "=== Clonando produccion -> staging ==="
echo "[1/5] Deteniendo Odoo staging..."
docker stop odoo-staging
echo "[2/5] Backup base de datos produccion..."
docker exec "$PROD_CONTAINER" pg_dump -U odoo "$PROD_DB" > "$BACKUP_FILE"
echo "[3/5] Restaurando en staging..."
docker exec "$STAGING_CONTAINER" psql -U odoo -c "DROP DATABASE IF EXISTS $STAGING_DB;" postgres
docker exec "$STAGING_CONTAINER" psql -U odoo -c "CREATE DATABASE $STAGING_DB;" postgres
docker exec -i "$STAGING_CONTAINER" psql -U odoo "$STAGING_DB" < "$BACKUP_FILE"
echo "[4/5] Copiando filestore..."
docker run --rm -v "${PROD_DATA_VOL}:/prod:ro" -v "${STAGING_DATA_VOL}:/staging" alpine sh -c "rm -rf /staging/filestore && cp -r /prod/filestore /staging/filestore && mv /staging/filestore/amunet_prod /staging/filestore/Amunet_testing"
echo "[5/5] Reiniciando Odoo staging..."
docker start odoo-staging
rm -f "$BACKUP_FILE"
echo "=== Listo! staging.fc.amunet.com.mx tiene datos frescos ==="
