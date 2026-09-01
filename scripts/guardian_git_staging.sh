#!/usr/bin/env bash
# guardian_git_staging.sh - Vigila que no se pierda trabajo en el git de staging.
# Detecta: archivos sin commitear, commits sin pushear, stashes abiertos,
#          ramas sin integrar y modulos instalados sin codigo en disco.
# Solo LEE. Nunca modifica el repo ni el arbol de trabajo.
# Cron: diario 22:00 (crontab de agentia-odoo)
# Creado: 2026-08-31

REPO=/opt/odoo/staging
DEST="${DEST:-fernando.ruiz@amunet.com.mx,desarrollo@amunet.com.mx}"
DIAS_SIN_INTEGRAR=${DIAS_SIN_INTEGRAR:-14}
LOG=/home/agentia-odoo/scripts/guardian_git_staging.log
MAILER=/home/agentia-odoo/scripts/_send_mail.py

log(){ echo "[$(date -Iseconds)] $*" >> "$LOG"; }

cd "$REPO" 2>/dev/null || { log "ERROR: no existe $REPO"; exit 1; }
git fetch origin -q 2>/dev/null

HALLAZGOS=""
N=0

# --- 1) Archivos sin commitear -------------------------------------------
SIN_COMMIT=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$SIN_COMMIT" -gt 0 ]; then
    N=$((N+1))
    DETALLE=$(git status --porcelain 2>/dev/null | head -25)
    HALLAZGOS="${HALLAZGOS}
[1] ARCHIVOS SIN GUARDAR: ${SIN_COMMIT}
    Estos cambios NO estan en ninguna rama. Si alguien cambia de rama, SE PIERDEN.
${DETALLE}
"
fi

# --- 2) Commits sin subir a GitHub ---------------------------------------
PEND=""
while read -r b; do
    [ -z "$b" ] && continue
    [ "$b" = "main" ] && continue
    if git show-ref --verify --quiet "refs/remotes/origin/$b"; then
        n=$(git rev-list --count "origin/$b..$b" 2>/dev/null)
        [ "$n" -gt 0 ] && PEND="${PEND}    - ${b}: ${n} commit(s) sin subir
"
    else
        PEND="${PEND}    - ${b}: NO existe en GitHub (solo en este servidor)
"
    fi
done < <(git for-each-ref --format='%(refname:short)' refs/heads)

if [ -n "$PEND" ]; then
    N=$((N+1))
    HALLAZGOS="${HALLAZGOS}
[2] TRABAJO SIN SUBIR A GITHUB:
    Si el servidor falla, esto no se puede recuperar.
${PEND}"
fi

# --- 3) Stashes abiertos (cajas temporales olvidadas) --------------------
NSTASH=$(git stash list 2>/dev/null | wc -l | tr -d ' ')
if [ "$NSTASH" -gt 0 ]; then
    N=$((N+1))
    DETALLE=$(git stash list --format='    %gd | %cr | %s' 2>/dev/null | head -15)
    HALLAZGOS="${HALLAZGOS}
[3] CAJAS TEMPORALES (stash) ABIERTAS: ${NSTASH}
    Un stash NO se sube a GitHub. Es la forma mas comun de perder trabajo.
    Regla: no usar 'git stash'. Guardar como commit en una rama.
${DETALLE}
"
fi

# --- 4) Ramas sin integrar en staging, con antiguedad --------------------
VIEJAS=""
LIMITE=$(date -d "-${DIAS_SIN_INTEGRAR} days" +%s 2>/dev/null)
while read -r b; do
    [ -z "$b" ] && continue
    case "$b" in main|staging|rescue/*|backup*|promote*|pm/backlog) continue ;; esac
    ts=$(git log -1 --format='%ct' "$b" 2>/dev/null)
    [ -z "$ts" ] && continue
    if [ "$ts" -lt "$LIMITE" ]; then
        dias=$(( ( $(date +%s) - ts ) / 86400 ))
        VIEJAS="${VIEJAS}    - ${b}: ${dias} dias sin integrar
"
    fi
done < <(git branch --no-merged origin/staging --format='%(refname:short)' 2>/dev/null)

if [ -n "$VIEJAS" ]; then
    N=$((N+1))
    HALLAZGOS="${HALLAZGOS}
[4] RAMAS SIN INTEGRAR A 'staging' (mas de ${DIAS_SIN_INTEGRAR} dias):
    Mientras mas tiempo pasan sueltas, mas dificil y riesgoso es juntarlas.
${VIEJAS}"
fi

# --- 5) Modulos instalados en la BD pero SIN codigo en disco -------------
FANTASMA=""
while read -r m; do
    m=$(echo "$m" | tr -d ' ')
    [ -z "$m" ] && continue
    [ -d "${REPO}/addons/${m}" ] || FANTASMA="${FANTASMA}    - ${m}
"
done < <(docker exec odoo-staging-db psql -U odoo -d Amunet_testing -t -c \
        "SELECT name FROM ir_module_module WHERE name LIKE 'amunet_%' AND state='installed';" 2>/dev/null)

if [ -n "$FANTASMA" ]; then
    N=$((N+1))
    HALLAZGOS="${HALLAZGOS}
[5] MODULOS INSTALADOS EN ODOO PERO SIN CODIGO EN DISCO:
    Odoo cree que existen pero su codigo no esta. Provoca errores y
    hace que el clon de produccion truene.
${FANTASMA}"
fi

# --- 6) Modulos ATORADOS en un estado intermedio -------------------------
# Un modulo que se queda en 'to install' / 'to upgrade' / 'to remove' rompe la
# carga del registro en CADA arranque: Odoo revienta antes de servir trafico,
# el contenedor sale con codigo 0 sin dejar rastro en el log de docker, y nginx
# responde 502. Paso el 2026-09-01 con amunet_iso13485_lifecycle.
# Se desatora con: modulo.button_reset_state()
ATORADOS=$(docker exec odoo-staging-db psql -U odoo -d Amunet_testing -t -A -F' -> ' -c \
    "SELECT name, state FROM ir_module_module
     WHERE state NOT IN ('installed','uninstalled','uninstallable')
     ORDER BY name;" 2>/dev/null)

if [ -n "$ATORADOS" ]; then
    N=$((N+1))
    DETALLE=$(echo "$ATORADOS" | sed 's/^/    - /')
    HALLAZGOS="${HALLAZGOS}
[6] MODULOS ATORADOS EN UN ESTADO INTERMEDIO:
    Esto tumba staging: Odoo falla al cargar el registro en cada arranque y
    nginx responde 502. El contenedor sale con codigo 0, asi que el log de
    docker queda VACIO y parece que no paso nada.
    Se arregla con: env['ir.module.module'].search([('name','=','<modulo>')]).button_reset_state()
${DETALLE}
"
fi

# --- 7) Staging responde? ------------------------------------------------
CODIGO=$(docker exec odoo-staging curl -s -o /dev/null -w '%{http_code}' \
         http://localhost:8069/web/health 2>/dev/null)
if [ "$CODIGO" != "200" ]; then
    N=$((N+1))
    ESTADO_CONT=$(docker ps -a --filter name=odoo-staging --format '{{.Names}}: {{.Status}}' 2>/dev/null | head -3)
    HALLAZGOS="${HALLAZGOS}
[7] STAGING NO RESPONDE (HTTP ${CODIGO:-sin respuesta}):
    Revisar el log INTERNO de Odoo, no el de docker:
      docker exec odoo-staging tail -50 /var/log/odoo/odoo-server.log
${ESTADO_CONT}
"
fi

# --- Resultado -----------------------------------------------------------
if [ "$N" -eq 0 ]; then
    log "OK: sin hallazgos (arbol limpio)"
    exit 0
fi

RAMA=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
SUBJECT="[Odoo Amunet] Guardian git staging: ${N} hallazgo(s) que pueden costar trabajo"
BODY="Revision automatica del repositorio de staging (/opt/odoo/staging).

Rama actualmente abierta: ${RAMA}
Fecha: $(date '+%d.%m.%y %I:%M %p')

Se encontraron ${N} situacion(es) que ponen en riesgo el trabajo:
${HALLAZGOS}

---------------------------------------------------------------------
QUE HACER
---------------------------------------------------------------------
  1. Guardar lo pendiente:   cd /opt/odoo/staging && git add -A && git commit -m \"...\"
  2. Subirlo a GitHub:       git push origin \$(git rev-parse --abbrev-ref HEAD)
  3. Si hay stashes, pedir al agente PM que los rescate a una rama.
  4. Si hay modulos sin codigo, avisar al agente PM (bloquea el clon).

Reglas para que esto no se repita:
  - No usar 'git stash'. Guardar siempre como commit.
  - Al cerrar la jornada: commit + push, sin excepcion.
  - Integrar cada rama a 'staging' en dias, no en meses.

-- Guardian automatico del git de staging"

python3 "$MAILER" --to "$DEST" --subject "$SUBJECT" --body "$BODY" >/dev/null 2>&1 \
    && log "ALERTA enviada a $DEST (${N} hallazgos)" \
    || log "ERROR al enviar correo (${N} hallazgos)"

exit 0
