#!/bin/bash
# Chequeo diario de la configuracion de Control de Calidad.
#
# POR QUE EXISTE (18-sep-2026)
# Ese dia se encontraron 211 especificaciones y 11 parametros con active en
# NULL. Existian con sus valores correctos pero NO aparecian en el analisis:
# el bloque salia vacio y NADIE SE ENTERABA, porque no hay error ni aviso.
# Consecuencia: 24 analisis cerrados se aprobaron sin ejecutar un control
# que si estaba configurado. Se detecto barriendo a mano, por casualidad.
#
# Este chequeo busca esa familia de fallos silenciosos y avisa al buzon de
# desarrollo SOLO si encuentra algo.
#
# Cron: /etc/cron.d/chequeo_calidad (diario 07:30). Correr como agentia-odoo.
set -uo pipefail

DB=amunet_prod
CT=odoo-production-db
LOG=/home/agentia-odoo/logs/chequeo_calidad.log
mkdir -p "$(dirname "$LOG")"

q() { docker exec "$CT" psql -U odoo -d "$DB" -tAc "$1" 2>/dev/null | tr -d ' '; }
log() { echo "[$(date -Iseconds)] $*" >> "$LOG"; }

HALLAZGOS=""
add() { HALLAZGOS="${HALLAZGOS}$1"$'\n'; }

# 1. active en NULL (el defecto de 18-sep). Deberia ser imposible por el
#    NOT NULL, pero se vigila por si alguien lo quita.
for t in amunet_quality_parameter_specification_config \
         amunet_quality_parameter_product_rel \
         amunet_quality_point amunet_quality_check; do
    n=$(q "SELECT COUNT(*) FROM $t WHERE active IS NULL")
    [ "${n:-0}" -gt 0 ] && add "  - $t: $n registro(s) con active en NULL (invisibles)"
done

# 2. Bloques activos sin un solo renglon visible: el analisis nace con ese
#    bloque vacio.
n=$(q "SELECT COUNT(*) FROM amunet_quality_parameter_product_rel rel
       WHERE rel.active AND NOT EXISTS (
         SELECT 1 FROM amunet_quality_parameter_specification_config sc
         WHERE sc.product_parameter_rel_id=rel.id AND sc.active)")
[ "${n:-0}" -gt 0 ] && add "  - $n bloque(s) activos sin ninguna especificacion visible"

# 3. Analisis ABIERTOS y no archivados con menos renglones de los que hoy
#    corresponden: se crearon antes de que se arreglara su catalogo.
n=$(q "SELECT COUNT(*) FROM amunet_quality_check c
       JOIN product_product pp ON pp.id=c.product_id
       WHERE c.active AND c.state NOT IN ('done','cancelled','cancel')
         AND (SELECT COUNT(*) FROM amunet_quality_test_line_detail d
              JOIN amunet_quality_test_line tl ON tl.id=d.test_line_id
              WHERE tl.check_id=c.id)
           < (SELECT COUNT(*) FROM amunet_quality_parameter_specification_config sc
              JOIN amunet_quality_parameter_product_rel r ON r.id=sc.product_parameter_rel_id
              WHERE r.product_tmpl_id=pp.product_tmpl_id AND r.active AND sc.active)")
[ "${n:-0}" -gt 0 ] && add "  - $n analisis abierto(s) con menos renglones de los que corresponden"

# 4. Analisis que nacieron VACIOS: el producto no tenia parametros. Quedan
#    atrapados en borrador (paso con 18 de anticuerpos desde junio).
n=$(q "SELECT COUNT(*) FROM amunet_quality_check c
       WHERE c.active AND c.state NOT IN ('cancelled','cancel')
         AND NOT EXISTS (SELECT 1 FROM amunet_quality_test_line tl WHERE tl.check_id=c.id)")
[ "${n:-0}" -gt 0 ] && add "  - $n analisis SIN una sola linea (nacieron vacios)"

# 5. Rangos numericos sin valor util. Un 0-0 no es lo mismo que vacio:
#    evalua, y evalua mal.
n=$(q "SELECT COUNT(*) FROM amunet_quality_parameter_specification_config sc
       JOIN amunet_quality_parameter_product_rel r ON r.id=sc.product_parameter_rel_id
       WHERE r.active AND sc.active AND sc.evaluation_type='numeric_range'
         AND COALESCE(sc.min_value,0)=0 AND COALESCE(sc.max_value,0)=0")
[ "${n:-0}" -gt 0 ] && add "  - $n especificacion(es) numericas con rango vacio o en 0-0"

# 6. Productos con punto de calidad y el flag de recepcion apagado: el punto
#    no dispara nada. El codigo ya lo sincroniza, esto vigila las excepciones.
n=$(q "SELECT COUNT(DISTINCT pp.id)
       FROM amunet_quality_point qp
       JOIN amunet_quality_point_product_product_rel r ON r.amunet_quality_point_id=qp.id
       JOIN product_product pp ON pp.id=r.product_product_id
       JOIN product_template pt ON pt.id=pp.product_tmpl_id
       WHERE qp.active AND pt.active AND NOT pt.qc_required")
[ "${n:-0}" -gt 0 ] && add "  - $n producto(s) con punto de calidad y qc_required apagado"

if [ -z "$HALLAZGOS" ]; then
    log "sin hallazgos"
    exit 0
fi

log "HALLAZGOS:"$'\n'"$HALLAZGOS"
/home/agentia-odoo/scripts/aviso_area.sh desarrollo desarrollo \
  "Chequeo de calidad: $(echo "$HALLAZGOS" | grep -c '^  -') hallazgo(s)" \
"El chequeo diario de configuracion de Control de Calidad encontro esto en
produccion:

$HALLAZGOS
Que significa cada uno y por que importa:

  - active en NULL: el registro existe con sus valores pero NO aparece en el
    analisis. Es el fallo del 18-sep-2026 que dejo 24 analisis cerrados sin
    un control configurado. No deberia volver a ocurrir (las columnas tienen
    NOT NULL desde entonces); si aparece, alguien quito la proteccion.

  - Bloques sin especificacion: el analisis muestra el titulo del bloque y
    debajo no hay nada que capturar.

  - Analisis con menos renglones: se crearon antes de que se arreglara el
    catalogo del producto. Los renglones se copian al crear el analisis y
    quedan congelados; no se rellenan solos.

  - Analisis sin una sola linea: el producto no tenia parametros cuando se
    genero. Quedan atrapados en borrador.

  - Rangos en 0-0: distinto de vacio. El sistema lo evalua y lo evalua mal.

  - Punto de calidad con el flag apagado: el punto no dispara ningun analisis.

Revisar con calma; ninguno de estos produce error visible, por eso el chequeo." \
  >> "$LOG" 2>&1
