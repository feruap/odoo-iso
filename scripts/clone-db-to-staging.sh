#!/bin/bash
# clone-db-to-staging.sh - Copia exacta de produccion a staging
set -e
PROD_CONTAINER="odoo-production-db"
STAGING_CONTAINER="odoo-staging-db"
PROD_DB="odoo_production"
STAGING_DB="amunet_testing"
PROD_DATA_VOL="production_odoo-production-data"
STAGING_DATA_VOL="staging_odoo-staging-data"
BACKUP_FILE="/tmp/backup_prod.dump"
CONTAINER_BACKUP="/tmp/restore_prod.dump"

echo "=== Clonando produccion ($PROD_DB) -> staging ($STAGING_DB) ==="

echo "[1/5] Deteniendo Odoo staging..."
docker stop odoo-staging

echo "[2/5] Dump de $PROD_DB (modo seguro)..."
docker exec "$PROD_CONTAINER" pg_dump -F custom --no-owner --no-privileges -U odoo -f /tmp/backup_prod_internal.dump "$PROD_DB"
docker cp "${PROD_CONTAINER}:/tmp/backup_prod_internal.dump" "$BACKUP_FILE"
docker exec "$PROD_CONTAINER" rm -f /tmp/backup_prod_internal.dump
echo "Dump completado: $(du -sh $BACKUP_FILE | cut -f1)"

echo "[3/5] Restaurando como $STAGING_DB en staging..."
docker exec "$STAGING_CONTAINER" psql -U odoo -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${STAGING_DB}' AND pid <> pg_backend_pid();" postgres
docker exec "$STAGING_CONTAINER" psql -U odoo -c "DROP DATABASE IF EXISTS \"$STAGING_DB\" WITH (FORCE);" postgres
docker exec "$STAGING_CONTAINER" psql -U odoo -c "CREATE DATABASE \"$STAGING_DB\";" postgres
docker cp "$BACKUP_FILE" "${STAGING_CONTAINER}:${CONTAINER_BACKUP}"
echo "Ejecutando pg_restore (los warnings de roles son normales)..."
docker exec "$STAGING_CONTAINER" pg_restore -v -U odoo -d "$STAGING_DB" --no-owner --no-privileges "$CONTAINER_BACKUP" 2>&1 | grep -v "^pg_restore: creating" || true
docker exec "$STAGING_CONTAINER" rm -f "$CONTAINER_BACKUP"
rm -f "$BACKUP_FILE"
echo "Verificando tablas restauradas..."
docker exec "$STAGING_CONTAINER" psql -U odoo -d "$STAGING_DB" -c "SELECT count(*) as tablas FROM information_schema.tables WHERE table_schema='public';"

echo "[4/5] Copiando filestore y corrigiendo permisos..."
echo "--- Diagnostico: estructura del volumen de produccion ---"
docker run --rm -v "${PROD_DATA_VOL}:/prod:ro" alpine sh -c "find /prod -maxdepth 3 -type d | head -20"
echo "--- Fin diagnostico ---"
docker run --rm -v "${PROD_DATA_VOL}:/prod:ro" -v "${STAGING_DATA_VOL}:/staging" alpine sh -c \
  "rm -rf /staging/filestore/${STAGING_DB} && \
   mkdir -p /staging/filestore && \
   if [ -d /prod/filestore/odoo_production ]; then \
     echo 'Copiando filestore/odoo_production -> filestore/${STAGING_DB}'; \
     cp -r /prod/filestore/odoo_production /staging/filestore/${STAGING_DB}; \
   elif [ -d /prod/filestore/${PROD_DB} ]; then \
     echo 'Copiando filestore/${PROD_DB} -> filestore/${STAGING_DB}'; \
     cp -r /prod/filestore/${PROD_DB} /staging/filestore/${STAGING_DB}; \
   else \
     echo 'WARN: No se encontro filestore de produccion'; find /prod/filestore -maxdepth 1 -type d; \
   fi && \
   chown -R 100:101 /staging/filestore"

echo "[4.5/5] Limpiando cache de assets..."
docker exec "$STAGING_CONTAINER" psql -U odoo -d "$STAGING_DB" -c "DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%';" || true

echo "[5/5] Arrancando Odoo y actualizando modulos..."
docker start odoo-staging
echo "Esperando que Odoo este listo..."
for i in $(seq 1 24); do
  if docker exec odoo-staging curl -sf http://localhost:8069/web/health > /dev/null 2>&1; then
    echo "Odoo listo despues de $((i * 5))s"
    break
  fi
  echo "  Intento $i/24, esperando 5s..."
  sleep 5
done
docker exec odoo-staging bash -c "odoo -c /etc/odoo/odoo.conf -d ${STAGING_DB} -u all --stop-after-init --db_host \$HOST --db_port \$PORT --db_user \$USER --db_password \$PASSWORD"
docker compose -f /opt/odoo/staging/docker-compose.staging.yml restart web-staging
echo "=== Listo! staging.fc.amunet.com.mx es copia exacta de produccion ==="
