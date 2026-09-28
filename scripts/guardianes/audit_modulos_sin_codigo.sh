#!/usr/bin/env bash
# Revision diaria: modulos instalados cuyo CODIGO no existe, y modulos en
# disco sin versionar.
#
# Por que existe: el 07-sep-2026 esto paso TRES veces en un dia y siempre lo
# descubrio un usuario, no el sistema:
#   - un `git stash --include-untracked` se llevo del disco
#     amunet_almacen_distribucion y amunet_soluciones_kiosco (instalados);
#   - un `rm -rf` que fallo por permisos dejo amunet_quality a medias;
#   - una limpieza aparto amunet_almacen_distribucion a /opt/odoo/backups y
#     el siguiente build salio sin el.
# En los tres casos la BD seguia diciendo "installed" y Odoo no avisaba: la
# pantalla simplemente reventaba con "Invalid field ... on ...".
#
# Corre como agentia-odoo. NUNCA como root (git como root en esos repos es
# justo lo que rompio los permisos ese dia).
set -uo pipefail

DEST_EMAIL="${DEST_EMAIL:-fernando.ruiz@amunet.com.mx}"
LOG=/home/agentia-odoo/scripts/audit_modulos_sin_codigo.log
INBOX=/home/agentia-odoo/inboxes/desarrollo/inbox
HALLAZGOS=""

revisar_entorno() {
    local nombre="$1" contenedor="$2" contenedor_db="$3" base="$4" ruta="$5"
    local instalados faltan_disco faltan_cont sin_git

    docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$contenedor" || {
        HALLAZGOS+=$'\n'"[$nombre] el contenedor $contenedor no esta corriendo"
        return
    }

    instalados=$(docker exec "$contenedor_db" psql -U odoo -d "$base" -t -A -c \
        "SELECT name FROM ir_module_module WHERE state='installed' AND name LIKE 'amunet%' ORDER BY name;" 2>/dev/null)
    [ -z "$instalados" ] && { HALLAZGOS+=$'\n'"[$nombre] no se pudo consultar la base $base"; return; }

    faltan_disco=""; faltan_cont=""
    while read -r m; do
        [ -z "$m" ] && continue
        # No basta con que exista la carpeta: el 07-sep amunet_iso13485_lifecycle
        # tenia carpeta con 2 archivos y la BD lo daba por instalado con 7
        # modelos. Un modulo real trae manifest, __init__ y algo mas.
        if [ ! -d "$ruta/$m" ]; then
            faltan_disco+=" $m"
        elif [ ! -f "$ruta/$m/__manifest__.py" ]; then
            faltan_disco+=" $m(sin-manifest)"
        elif [ "$(find "$ruta/$m" -type f ! -name '*.pyc' 2>/dev/null | wc -l)" -lt 3 ]; then
            faltan_disco+=" $m(carpeta-hueca)"
        fi
        docker exec "$contenedor" test -d "/opt/amunet-addons/$m" 2>/dev/null || faltan_cont+=" $m"
    done <<< "$instalados"

    [ -n "$faltan_disco" ] && HALLAZGOS+=$'\n'"[$nombre] INSTALADOS SIN CODIGO EN DISCO:$faltan_disco"
    [ -n "$faltan_cont" ]  && HALLAZGOS+=$'\n'"[$nombre] INSTALADOS Y NO ESTAN EN EL CONTENEDOR (la pantalla va a reventar):$faltan_cont"

    # Modulos en disco que git no sigue: a un `git stash -u` de desaparecer.
    #
    # Antes esto miraba CUALQUIER archivo sin seguir bajo addons/, se quedaba con
    # el nombre del modulo y lo reportaba como "en disco sin versionar". Un solo
    # .bak olvidado adentro bastaba para acusar a un modulo entero que si estaba
    # completo en git: amunet_vencimientos salio 3 dias seguidos (26 al 28-sep-2026)
    # con sus 16 archivos versionados, por un rules.xml.bak. Una alarma que miente
    # a diario le ensena a la gente a ignorarla, y el dia que sea de verdad nadie
    # va a mirar.
    #
    # Ahora se separan los dos casos, que tienen gravedad distinta:
    #   - el modulo NO tiene ni un archivo seguido por git  -> se pierde entero
    #   - archivos sueltos dentro de un modulo versionado   -> solo esos archivos
    local repo_git="$ruta/.." mods_fuera="" files_sueltos="" rel mod
    if [ -d "$repo_git/.git" ]; then
        while IFS= read -r rel; do
            [ -z "$rel" ] && continue
            mod=$(printf '%s' "$rel" | cut -d/ -f2)
            if [ -z "$(cd "$repo_git" && git ls-files "addons/$mod/" 2>/dev/null | head -1)" ]; then
                mods_fuera+=" $mod"
            else
                files_sueltos+=" $rel"
            fi
        done <<< "$(cd "$repo_git" && git status --porcelain --untracked-files=all addons/ 2>/dev/null \
                    | sed -n 's/^?? //p')"
        mods_fuera=$(printf '%s' "$mods_fuera" | tr ' ' '\n' | sort -u | tr '\n' ' ')
        [ -n "${mods_fuera// /}" ] && HALLAZGOS+=$'\n'"[$nombre] MODULOS SIN VERSIONAR (un git stash/clean se los lleva ENTEROS):$mods_fuera"
        [ -n "${files_sueltos// /}" ] && HALLAZGOS+=$'\n'"[$nombre] archivos sueltos dentro de modulos que si estan en git (menor):$files_sueltos"
    fi
}

revisar_entorno "PRODUCCION" odoo-production odoo-production-db amunet_prod   /opt/odoo/production/addons
revisar_entorno "STAGING"    odoo-staging    odoo-staging-db    Amunet_testing /opt/odoo/staging/addons

FECHA=$(date '+%Y-%m-%d %H:%M')
if [ -z "$HALLAZGOS" ]; then
    echo "$FECHA  OK — todo modulo instalado tiene su codigo, y nada sin versionar" >> "$LOG"
    exit 0
fi

echo "$FECHA  HALLAZGOS:$HALLAZGOS" >> "$LOG"

CUERPO="Revision diaria de modulos de Odoo — $FECHA
$HALLAZGOS

QUE SIGNIFICA
  'Instalados sin codigo': la base dice que el modulo esta instalado pero su
  carpeta no existe. Odoo NO avisa; la pantalla revienta con
  'Invalid field ... on ...' cuando alguien entra. Se arregla restaurando la
  carpeta desde la rama y reconstruyendo la imagen.

  'MODULOS SIN VERSIONAR': el modulo corre pero git no sigue NI UNO de sus
  archivos. Un 'git stash --include-untracked' o un 'git clean' se lo lleva
  entero del disco, y la base va a seguir diciendo que esta instalado.
  Commitealo el mismo dia, aunque sea staging-only. Esto es lo grave.

  'archivos sueltos': el modulo SI esta en git; lo que no esta seguido son
  uno o varios archivos de adentro. Suelen ser respaldos (.bak, .orig) que
  alguien dejo, y entonces basta con borrarlos. Pero si es codigo de verdad,
  commitealo: nadie mas lo tiene.

-- Revision automatica de la sesion de desarrollo"

python3 /home/agentia-odoo/scripts/_send_mail.py \
    --to "$DEST_EMAIL" \
    --subject "[Odoo Amunet] Modulos instalados sin codigo — revision diaria" \
    --body "$CUERPO" >/dev/null 2>&1

# Dejar tambien el aviso en el buzon, para que la sesion lo vea al abrir.
mkdir -p "$INBOX"
ID="msg-$(date -u +%Y%m%dT%H%M%SZ)-audit-modulos"
{
    echo "---"; echo "id: $ID"; echo "from: sistema"; echo "to: desarrollo"
    echo "subject: Revision diaria — hay modulos instalados sin codigo"
    echo "created_at: $(date -Iseconds)"; echo "---"; echo
    echo "$CUERPO"
} > "$INBOX/${ID}.md"
chmod 660 "$INBOX/${ID}.md" 2>/dev/null
exit 1
