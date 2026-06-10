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

# 2. RAMP masivo (basado en número de ventanas de la descripción, via SQL directo)
docker exec odoo-staging-db psql -U odoo -d Amunet_testing -c "
UPDATE product_template pt
SET
  report_document_code = CASE
    WHEN (regexp_match(description->>'en_US', 'de (\d+) ventana'))[1]::int % 2 = 0 THEN 'RAMP-005'
    ELSE 'RAMP-004'
  END,
  certificate_document_code = CASE
    WHEN (regexp_match(description->>'en_US', 'de (\d+) ventana'))[1]::int % 2 = 0 THEN 'CERMP-005'
    ELSE 'CERMP-004'
  END
WHERE categ_id IN (SELECT id FROM product_category WHERE name='Cartucho')
  AND description IS NOT NULL AND description::text NOT IN ('{}','null')
  AND description->>'en_US' ~ 'de \d+ ventana';" | grep -E "UPDATE"

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

# 7. MAVI-14: Control (C) = N/A fijo y Prueba (T) = alineación tira reactiva (MPCAR67/68)
docker exec odoo-staging-db psql -U odoo -d Amunet_testing -c "
UPDATE amunet_quality_parameter_specification_config
SET specification_name='Línea Control (C) — N/A: tira reactiva sin línea control',
    acceptance_criteria='N/A',
    binary_option_pass='Línea Control (C) — N/A: tira reactiva sin línea control N/A',
    binary_option_fail='Línea Control (C) — N/A: tira reactiva sin línea control No',
    write_date=NOW()
WHERE id IN (72247, 72258);
UPDATE amunet_quality_parameter_specification_config
SET specification_name='Alineación de la tira reactiva en el recuadro',
    acceptance_criteria='Sí',
    binary_option_pass='Alineación de la tira reactiva en el recuadro Sí',
    binary_option_fail='Alineación de la tira reactiva en el recuadro No',
    write_date=NOW()
WHERE id IN (72248, 72259);" | grep -E "UPDATE"

# 8. MAVI-09: Tiempo de migración = N/A fijo (MPCAR67/68, tira reactiva sin flujo capilar)
docker exec odoo-staging-db psql -U odoo -d Amunet_testing -c "
UPDATE amunet_quality_parameter_specification_config
SET specification_name='Tiempo de migración — N/A: tira reactiva sin flujo capilar',
    evaluation_type='ternary_with_na',
    acceptance_criteria='N/A',
    ternary_option_yes='Sí', ternary_option_no='No', ternary_option_na='N/A',
    nominal_value=NULL, min_value=NULL, max_value=NULL,
    write_date=NOW()
WHERE id IN (72246, 72257);" | grep -E "UPDATE"

# 9. MAVI-11: agregar UOM mm a Cierre, Largo y Ancho (MPCAR67/68)
docker exec odoo-staging-db psql -U odoo -d Amunet_testing -c "
UPDATE amunet_quality_parameter_specification_config SET uom_id=6, write_date=NOW()
WHERE id IN (72249,72250,72251,72260,72261,72262);
UPDATE amunet_quality_test_line_detail SET uom_id=6, write_date=NOW()
WHERE specification_config_id IN (72249,72250,72251,72260,72261,72262) AND uom_id IS NULL;" \
| grep -E "UPDATE"

# 10. MAVI-11: UOM mm para Cierre completo e Interna (Ventana) en TODOS los cartuchos
docker exec odoo-staging-db psql -U odoo -d Amunet_testing -c "
UPDATE amunet_quality_parameter_specification_config
SET uom_id=6, write_date=NOW()
WHERE specification_name = 'Cierre completo'
  AND evaluation_type = 'numeric_range' AND uom_id IS NULL;
UPDATE amunet_quality_parameter_specification_config
SET uom_id=6, write_date=NOW()
WHERE specification_name IN ('Interna (Ventana) Largo', 'Interna (Ventana) Ancho')
  AND evaluation_type = 'numeric_range' AND uom_id IS NULL;" \
| grep -E "UPDATE"

echo "=== TODOS LOS SCRIPTS COMPLETADOS ==="
