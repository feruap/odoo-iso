#!/bin/bash
# backup.sh - Backup diario de produccion (DB + filestore)
# Cron: 0 2 * * * /opt/odoo/scripts/backup.sh >> /var/log/odoo-backup.log 2>&1
set -e
PROD_CONTAINER="odoo-production-db"
PROD_DB="odoo_production"
PROD_DATA_VOL="production_odoo-production-data"
BACKUP_DIR="/opt/odoo/backups"
KEEP_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
echo "=== Backup Odoo produccion ($TIMESTAMP) ==="

echo "[1/3] Backup base de datos..."
DB_FILE="${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz"
docker exec "$PROD_CONTAINER" pg_dump -U odoo "$PROD_DB" | gzip > "$DB_FILE"
echo "      Guardado: $DB_FILE ($(du -sh $DB_FILE | cut -f1))"

echo "[2/3] Backup filestore..."
FS_FILE="${BACKUP_DIR}/filestore_${TIMESTAMP}.tar.gz"
docker run --rm -v "${PROD_DATA_VOL}:/data:ro" -v "${BACKUP_DIR}:/backups" alpine tar czf "/backups/filestore_${TIMESTAMP}.tar.gz" -C /data filestore
echo "      Guardado: $FS_FILE ($(du -sh $FS_FILE | cut -f1))"

echo "[3/3] Limpiando backups de mas de ${KEEP_DAYS} dias..."
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +${KEEP_DAYS} -delete
find "$BACKUP_DIR" -name "filestore_*.tar.gz" -mtime +${KEEP_DAYS} -delete
echo "      Backups actuales: $(ls $BACKUP_DIR | wc -l) archivos"

echo "=== Backup completado OK $(date) ==="
