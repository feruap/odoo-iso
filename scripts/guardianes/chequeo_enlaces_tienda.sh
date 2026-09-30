#!/usr/bin/env bash
# Chequeo diario de los enlaces PDF que la tienda ofrece al cliente.
#
# POR QUE EXISTE (30-sep-2026)
# Fernando reporto el 9-sep que el enlace "Ficha de seguridad" de TBDx-Net apuntaba a
# un PDF que ya no existia. Lo encontro navegando la tienda, de casualidad, y llevaba
# ahi semanas. Al barrer los 136 enlaces PDF de las fichas publicadas salieron 20
# rotos, y 6 de ellos son documentos NUESTROS: los manuales de antidoping de 4 drogas
# y de opiaceos, el de PSA semicuantitativa, el de hCG tira orina, el de Anti-IgG
# COVID y uno de hCG subido con el nombre mal (DMHCG02.pdf.pdf). Un cliente que compra
# esas pruebas le da a "descargar manual" y no baja nada. Nadie lo habia reportado.
#
# Lo que tienen en comun con los otros fallos silenciosos que vigilamos: el sistema no
# se rompe, no hay error, todo parece normal. El unico que lo nota es el cliente, y el
# cliente no reporta.
#
# ESTE CHEQUEO NO ARREGLA NADA: Odoo no puede escribir en la tienda -la llave es de
# solo lectura, a proposito desde el episodio del lote fantasma-. Detecta y avisa. El
# arreglo lo hace Fernando en WordPress. Lo que cambia es el tiempo: de semanas a un dia.
#
# Cron: /etc/cron.d/chequeo_enlaces_tienda (diario 06:45, antes del de calidad).
# Correr como agentia-odoo.
set -uo pipefail

LOG=/home/agentia-odoo/logs/chequeo_enlaces_tienda.log
ESTADO=/home/agentia-odoo/logs/chequeo_enlaces_tienda.estado
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
mkdir -p "$(dirname "$LOG")"
log() { echo "[$(date -Iseconds)] $*" >> "$LOG"; }

# --- 1. sacar los enlaces PDF de las fichas publicadas (por Odoo, que ya tiene la llave)
cat > "$TMP/extraer.py" <<'PY'
import json, re
b = env['amunet.woo.backend'].sudo().search([], limit=1)
if not b:
    print('SIN_BACKEND'); raise SystemExit
enlaces = {}
pagina = 1
while pagina <= 8:
    try:
        d, _r = b._wc_get('products', {'per_page': 50, 'page': pagina, 'status': 'publish'})
    except Exception as e:
        print('ERROR_TIENDA|%s' % str(e)[:120]); raise SystemExit
    if not d:
        break
    for p in d:
        txt = (p.get('description') or '') + ' ' + (p.get('short_description') or '')
        for u in re.findall(r'href="(https?://[^"]+\.pdf)"', txt):
            enlaces.setdefault(u, set()).add('%s %s' % (
                p.get('sku') or p.get('id'), (p.get('name') or '')[:34]))
    pagina += 1
print('OK|%s' % json.dumps({u: sorted(v)[:3] for u, v in enlaces.items()}))
PY
docker cp "$TMP/extraer.py" odoo-production:/tmp/chk_enlaces.py >/dev/null 2>&1
SALIDA=$(timeout 400 docker exec odoo-production bash -c 'odoo shell -c /etc/odoo/odoo.conf -d amunet_prod --no-http --db_host $HOST --db_port $PORT --db_user $USER --db_password $PASSWORD < /tmp/chk_enlaces.py' 2>/dev/null | grep -E '^(OK|SIN_BACKEND|ERROR_TIENDA)\|?' | head -1)

case "$SALIDA" in
  SIN_BACKEND) log "no hay backend de tienda configurado"; exit 0 ;;
  ERROR_TIENDA*) log "no se pudo leer la tienda: ${SALIDA#*|}"; exit 0 ;;
  OK\|*) echo "${SALIDA#OK|}" > "$TMP/enlaces.json" ;;
  *) log "respuesta inesperada al extraer enlaces"; exit 0 ;;
esac

# --- 2. probar cada enlace, distinguiendo "sitio caido" de "archivo faltante"
python3 - "$TMP/enlaces.json" "$TMP/rotos.txt" <<'PY'
import json, subprocess, sys, collections
enlaces = json.load(open(sys.argv[1]))
def probar(url):
    r = subprocess.run(['curl','-sL','-o','/dev/null','-w','%{http_code}','-A','Mozilla/5.0',
                        '--max-time','15', url], capture_output=True, text=True)
    return r.stdout.strip() or '000'

# Si la portada no responde, el sitio esta caido y no se avisa de 136 archivos.
if probar('https://www.amunet.com.mx/') not in ('200', '301', '302'):
    print('SITIO_CAIDO'); sys.exit(0)

rotos = []
for u, prods in sorted(enlaces.items()):
    code = probar(u)
    if code != '200':
        rotos.append((code, u, prods))
# Un dominio ajeno que no responde no es lo mismo que un documento nuestro que falta.
nuestros = [r for r in rotos if 'amunet.com.mx' in r[1]]
ajenos = [r for r in rotos if 'amunet.com.mx' not in r[1]]
with open(sys.argv[2], 'w') as fh:
    fh.write('TOTAL=%d\nROTOS=%d\nNUESTROS=%d\nAJENOS=%d\n' % (
        len(enlaces), len(rotos), len(nuestros), len(ajenos)))
    for etiqueta, grupo in (('NUESTRO', nuestros), ('EXTERNO', ajenos)):
        for code, u, prods in grupo:
            fh.write('%s|%s|%s|%s\n' % (etiqueta, code, u, '; '.join(prods)))
print('LISTO')
PY

[ -s "$TMP/rotos.txt" ] || { log "no se pudo probar los enlaces"; exit 0; }
grep -q SITIO_CAIDO "$TMP/rotos.txt" 2>/dev/null && { log "la tienda no responde; no se avisa"; exit 0; }

TOTAL=$(grep '^TOTAL=' "$TMP/rotos.txt" | cut -d= -f2)
ROTOS=$(grep '^ROTOS=' "$TMP/rotos.txt" | cut -d= -f2)
NUESTROS=$(grep '^NUESTROS=' "$TMP/rotos.txt" | cut -d= -f2)
AJENOS=$(grep '^AJENOS=' "$TMP/rotos.txt" | cut -d= -f2)
log "revisados $TOTAL enlaces: $ROTOS rotos ($NUESTROS nuestros, $AJENOS externos)"

[ "${ROTOS:-0}" -eq 0 ] && { log "todos sirven; sin aviso"; exit 0; }

# --- 3. avisar solo si la lista CAMBIO, para no repetir el mismo aviso cada dia
FIRMA=$(grep -E '^(NUESTRO|EXTERNO)\|' "$TMP/rotos.txt" | cut -d'|' -f1-3 | sort | md5sum | cut -d' ' -f1)
if [ -f "$ESTADO" ] && [ "$(cat "$ESTADO")" = "$FIRMA" ]; then
  log "la misma lista de ayer; no se repite el aviso"
  exit 0
fi
echo "$FIRMA" > "$ESTADO"

CUERPO="El chequeo diario encontro enlaces PDF rotos en las fichas PUBLICADAS de la tienda.
Son documentos que la pagina le ofrece al cliente y que al descargar no existen.

    revisados: $TOTAL enlaces
    rotos:     $ROTOS   ($NUESTROS de amunet.com.mx, $AJENOS de otros sitios)
"
if [ "${NUESTROS:-0}" -gt 0 ]; then
  CUERPO="$CUERPO
=====================================================================
NUESTROS DOCUMENTOS -- estos son los que urgen
=====================================================================
Estan en nuestro servidor y faltan. Si es un manual, el cliente que compro esa prueba
no lo puede descargar.
"
  while IFS='|' read -r tipo code url prods; do
    [ "$tipo" = "NUESTRO" ] || continue
    CUERPO="$CUERPO
    HTTP $code  $(basename "$url")
         en: $prods"
  done < <(grep '^NUESTRO|' "$TMP/rotos.txt")
fi
if [ "${AJENOS:-0}" -gt 0 ]; then
  CUERPO="$CUERPO

=====================================================================
DOCUMENTOS DE OTROS SITIOS
=====================================================================
Guias, protocolos y articulos de terceros que cambiaron de direccion o desaparecieron.
Conviene quitarlos o actualizarlos, pero no son material nuestro.
"
  while IFS='|' read -r tipo code url prods; do
    [ "$tipo" = "EXTERNO" ] || continue
    CUERPO="$CUERPO
    HTTP $code  $(basename "$url")
         en: $prods"
  done < <(grep '^EXTERNO|' "$TMP/rotos.txt")
fi
CUERPO="$CUERPO

=====================================================================
QUE HACER, Y QUIEN
=====================================================================
El arreglo es en WordPress y lo hace Fernando: Odoo no puede escribir en la tienda, su
llave es de solo lectura a proposito.

  - documento nuestro que falta  ->  volver a subir el PDF con el mismo nombre
  - documento externo            ->  quitar el enlace o apuntarlo a la direccion nueva
  - ficha de seguridad que no existe -> generar el documento o retirar el enlace;
    mejor sin enlace que con uno roto en un producto sanitario

Los codigos: 404 el archivo no esta, 000 el dominio no responde, 301 redirige a otro
lado (sirve pero no es la direccion anunciada).

Este aviso no se repite mientras la lista sea la misma. Vuelve a salir cuando cambie."

~/scripts/aviso_area.sh desarrollo fernando "Enlaces PDF rotos en la tienda: $ROTOS de $TOTAL ($NUESTROS nuestros)" "$CUERPO" >/dev/null 2>&1
log "aviso enviado a fernando"
