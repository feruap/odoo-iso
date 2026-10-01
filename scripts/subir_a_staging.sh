#!/usr/bin/env bash
# Sube cambios a origin/staging SIN dejar /opt/odoo/staging divergido.
#
# Uso:  ~/scripts/subir_a_staging.sh <mensaje.txt> <ruta> [ruta...]
#       las rutas son relativas a /opt/odoo/staging
#
# POR QUE EXISTE (01-oct-2026). El CI de staging llevaba todo el dia en rojo:
#
#     Your branch and 'origin/staging' have diverged,
#     and have 13 and 20 different commits each, respectively.
#     fatal: Not possible to fast-forward, aborting.
#
# La causa era el metodo, no un bug. Se commiteaba EN /opt/odoo/staging -- que es el
# directorio que el contenedor sirve por bind mount, asi que es donde hay que editar
# para probar- y despues se subia por cherry-pick desde un worktree sobre
# origin/staging. El cherry-pick crea arriba un commit con OTRO SHA, y el local se
# queda con el suyo: cada cambio del dia sumaba una divergencia.
#
# El `git pull --ff-only` del workflow entonces falla, y falla A PROPOSITO: esta puesto
# para que un deploy conflictivo se caiga de forma ruidosa en vez de pasar por encima
# del trabajo sin commitear que haya en el servidor. El propio deploy.yml lo advierte:
#
#     # WARNING TO AI AGENTS: Do NOT replace `git pull --ff-only` with
#     # `git reset --hard`. Fast-forward-only protects in-flight uncommitted work
#
# El costo de dejarlo roto no es cosmetico: cuando TODO esta rojo, un fallo de verdad
# no se distingue del ruido.
#
# QUE HACE ESTE SCRIPT
#   1. Commitea en un worktree propio sobre origin/staging, nunca en el compartido.
#   2. Empuja a origin/staging.
#   3. Alinea /opt/odoo/staging con origin SIN tocar el trabajo sin commitear de las
#      otras once sesiones, y solo si es seguro.
#
# LO QUE NO HACE, y es deliberado: no usa `git reset --hard` ni `git clean`. Esos
# comandos retiran del disco los archivos que git no sigue, y asi se perdieron dos
# modulos completos el 07-sep-2026.
set -euo pipefail

REPO=/opt/odoo/staging
MSG="${1:-}"; shift || true
rojo()  { printf '\033[31m%s\033[0m\n' "$*"; }
verde() { printf '\033[32m%s\033[0m\n' "$*"; }

[ -n "$MSG" ] && [ -r "$MSG" ] || { rojo "Falta el archivo de mensaje."; echo 'Uso: subir_a_staging.sh <mensaje.txt> <ruta> [ruta...]'; exit 1; }
[ "$#" -gt 0 ] || { rojo "No diste ninguna ruta que subir."; exit 1; }

cd "$REPO"
for r in "$@"; do
  [ -e "$r" ] || { rojo "No existe en $REPO: $r"; exit 1; }
done

SCRATCH="${SCRATCH_DIR:-/tmp/claude-1001/subir_a_staging}"
WT="$SCRATCH/wt.$$"
RAMA="tmp/subir.$$"
limpiar() { cd "$REPO"; git worktree remove --force "$WT" 2>/dev/null || true; git branch -D "$RAMA" >/dev/null 2>&1 || true; }
trap limpiar EXIT

git fetch origin --quiet
rm -rf "$WT"; mkdir -p "$SCRATCH"
git worktree prune
git worktree add --quiet -B "$RAMA" "$WT" origin/staging

# Se copian SOLO las rutas pedidas: nada de "git add -A", que arrastraria trabajo ajeno.
for r in "$@"; do
  mkdir -p "$WT/$(dirname "$r")"
  cp -a "$r" "$WT/$r"
done

cd "$WT"
git add -- "$@"
if git diff --cached --quiet; then
  verde "Nada que subir: lo que mandaste ya esta igual en origin/staging."
  exit 0
fi
git commit --quiet -F "$MSG"
SHA=$(git rev-parse --short HEAD)
git push --quiet origin "HEAD:staging"
verde "Subido a origin/staging: $SHA"
git --no-pager log -1 --format='   %s'

# ---- alinear el directorio compartido ----
cd "$REPO"
git fetch origin --quiet
if git merge-base --is-ancestor HEAD origin/staging; then
  git merge --ff-only origin/staging --quiet 2>/dev/null || true
  verde "El directorio compartido ya va al dia (fast-forward limpio)."
  exit 0
fi

# Hay commits locales. Solo se alinea si TODO su contenido esta ya en origin: si alguien
# dejo trabajo commiteado y sin subir, el reset le quitaria el commit del historial.
PENDIENTE=""
for c in $(git log origin/staging..HEAD --format=%h); do
  for f in $(git show --name-only --format= "$c" | grep . || true); do
    git diff --quiet "$c" origin/staging -- "$f" 2>/dev/null || PENDIENTE="$PENDIENTE $c:$f"
  done
done

if [ -n "$PENDIENTE" ]; then
  rojo "NO se alinea el directorio: hay commits locales con contenido que no esta en origin."
  echo "   Es trabajo de otra sesion sin subir. Avisale antes de tocar nada:"
  for x in $PENDIENTE; do echo "     $x"; done
  echo "   (tu cambio SI quedo subido: $SHA)"
  exit 0
fi

ANTES=$(git status --porcelain | grep -c '^ M\|^??' || true)
git reset --mixed origin/staging >/dev/null
# El reset deja como "borrados" los archivos que estan en origin y no en el disco
# (tipico de scripts que otra sesion creo en SU worktree y nunca pasaron por aqui).
# Se traen de origin: anade lo que falta, no sobrescribe nada ajeno.
FALTANTES=$(git status --porcelain | awk '$1=="D"{print $2}')
[ -n "$FALTANTES" ] && git checkout -- $FALTANTES && echo "   traidos de origin $(echo "$FALTANTES" | wc -l) archivo(s) que faltaban en el disco"
DESPUES=$(git status --porcelain | grep -c '^ M\|^??' || true)
verde "Directorio compartido alineado con origin/staging."
echo "   trabajo sin commitear de otras sesiones: antes=$ANTES  ahora=$DESPUES"
[ "$ANTES" = "$DESPUES" ] || rojo "   OJO: cambio ese numero, revisa 'git status' antes de seguir."
