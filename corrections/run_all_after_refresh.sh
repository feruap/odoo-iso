#!/bin/bash
# Re-ejecuta todos los scripts de datos después de un refresco de staging
# Orden importante: primero RAMP, luego info adicional, luego empleados

NETWORK="staging_odoo-staging-net"
DB_HOST="odoo-staging-db"
DB_PASS="odoo_stg_2024_secure"
IMAGE="odoo:19.0-amunet-staging"
ADDONS="/opt/odoo/staging/addons"
CORR="/opt/odoo/staging/corrections"
DOCX="/tmp/F-CC-007-001 Descripción y especficacion de cartuchos para pruebas rápidas.docx"

run_shell() {
    local script=$1
    echo "=== Ejecutando: $(basename $script) ==="
    docker run --rm \
      --network $NETWORK \
      -e HOST=$DB_HOST -e PORT=5432 -e USER=odoo -e PASSWORD=$DB_PASS \
      -v $ADDONS:/opt/amunet-addons \
      -v $script:/tmp/script.py \
      $IMAGE \
      bash -c 'odoo shell -c /etc/odoo/odoo.conf -d Amunet_testing --no-http --logfile="" < /tmp/script.py 2>&1' \
      | grep -E "OK|Actualiz|Listo|ERROR|Corregid|Found|added|configurad" | tail -5
}

run_python() {
    local script=$1
    echo "=== Ejecutando: $(basename $script) ==="
    docker run --rm \
      --network $NETWORK \
      -v "$DOCX":/tmp/F-CC-007-001_full.docx \
      -v $script:/tmp/script.py \
      $IMAGE \
      bash -c 'pip install python-docx -q --break-system-packages && python3 /tmp/script.py' 2>&1 \
      | grep -E "datos|ACTUALIZ|Listo|ERROR" | tail -5
}

# 1. Descripciones (necesitan el docx)
run_python "$CORR/20260605_72_gen_descriptions_direct.py"

# 2. RAMP masivo (basado en descripciones)
run_shell "$CORR/20260603_66_fix_ramp_codes_masivo.py"

# 3. Info adicional (largo, ancho, CV)
run_shell "$CORR/20260604_67_add_additional_info_cartuchos.py"

# 4. Observaciones
run_shell "$CORR/20260604_69_add_observations_cartuchos.py"

# 5. Campos obligatorios
docker exec odoo-staging-db psql -U odoo -d Amunet_testing -c "
UPDATE amunet_quality_additional_info_config ac
SET required = true
FROM amunet_quality_additional_info_field aif
WHERE ac.field_id = aif.id AND aif.code IN ('external_length','external_width','cv_percent') AND ac.required = false;" \
| grep -E "UPDATE"

# 6. Códigos de empleado
docker exec odoo-staging-db psql -U odoo -d Amunet_testing -c "
UPDATE res_users SET employee_code='019' WHERE login='s.controldecalidad@amunet.com.mx';
UPDATE res_users SET employee_code='020' WHERE login='analista1cc@amunet.com.mx';
UPDATE res_users SET employee_code='005' WHERE login='analista2cc@amunet.com.mx';
SELECT login, employee_code FROM res_users WHERE login IN ('s.controldecalidad@amunet.com.mx','analista1cc@amunet.com.mx','analista2cc@amunet.com.mx');" \
2>&1 | grep -v "^--\|^ login"

echo "=== TODOS LOS SCRIPTS COMPLETADOS ==="
