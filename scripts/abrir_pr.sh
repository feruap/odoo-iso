#!/usr/bin/env bash
# Abre un PR a main sin depender de otra sesion.
#
# Uso:  ~/scripts/abrir_pr.sh "Titulo del PR" [rama] [cuerpo.md]
# Si no se da rama, usa la del directorio actual.
#
# POR QUE EXISTE: las sesiones de agente no tenian como abrir un PR. gh no esta
# instalado y el GITHUB_TOKEN de /opt/odoo/.env da 401 (caducado, y el archivo es
# de root). El token que si sirve vive en ~/.github_pat, y es del usuario
# agentia-odoo -- el mismo con el que corren TODAS las sesiones, asi que siempre
# estuvo al alcance de todas; solo no estaba escrito en ningun lado.
#
# LO QUE ADEMAS EVITA: dos veces el 29-sep-2026 una rama de otra sesion estaba
# creada sobre un main viejo, y su diff contra el main de hoy BORRABA archivos de
# otros agentes -- los 3 scripts de anexos de Calidad en un caso, dos de
# compras_tablero en el otro. Mergearlas se los habria llevado sin que nadie lo
# notara. Este script se NIEGA a abrir el PR en ese caso, y dice como arreglarlo.
set -euo pipefail

TITULO="${1:-}"; RAMA="${2:-}"; CUERPO_FILE="${3:-}"
REPO="feruap/odoo-iso"; TOKEN_FILE="$HOME/.github_pat"

rojo()  { printf '\033[31m%s\033[0m\n' "$*"; }
verde() { printf '\033[32m%s\033[0m\n' "$*"; }

[ -n "$TITULO" ] || { rojo "Falta el titulo."; echo 'Uso: abrir_pr.sh "Titulo" [rama] [cuerpo.md]'; exit 1; }
[ -r "$TOKEN_FILE" ] || { rojo "No puedo leer $TOKEN_FILE"; exit 1; }
TOKEN=$(tr -d ' \n' < "$TOKEN_FILE")

git rev-parse --git-dir >/dev/null 2>&1 || { rojo "No estas en un repo git."; exit 1; }
[ -n "$RAMA" ] || RAMA=$(git rev-parse --abbrev-ref HEAD)
case "$RAMA" in main|staging) rojo "No se abre PR de '$RAMA' a main."; exit 1 ;; esac

echo "Repo: $REPO    Rama: $RAMA"
git fetch origin -q 2>/dev/null || true

REF="origin/$RAMA"
git rev-parse --verify -q "$REF" >/dev/null 2>&1 || REF="$RAMA"
COMMITS=$(git rev-list origin/main.."$REF")
[ -n "$COMMITS" ] || { rojo "La rama no tiene commits sobre main."; exit 1; }

# --- el chequeo que importa: nada fuera de lo que tocaron sus commits ---
AJENOS=$(comm -23 \
  <(git diff --name-only origin/main "$REF" | sort -u) \
  <(for c in $COMMITS; do git show --name-only --format="" "$c"; done | sort -u) || true)

if [ -n "$AJENOS" ]; then
  rojo "ALTO: la rama esta vieja."
  echo
  echo "Su diff contra el main de ahora toca archivos que tus commits NO tocaron."
  echo "Mergearla asi los REVIERTE al estado viejo y borra el trabajo de quien"
  echo "los cambio despues:"
  echo
  echo "$AJENOS" | sed 's/^/    /'
  echo
  echo "Arreglalo rebaseando tu trabajo sobre el main de ahora:"
  echo
  echo "    D=\$(mktemp -d) && git clone -q /opt/odoo/staging \$D/r && cd \$D/r"
  echo "    git remote set-url origin git@github.com:$REPO.git"
  echo "    git fetch origin -q"
  echo "    git checkout -B promo/$RAMA origin/main"
  for c in $(echo "$COMMITS" | tac); do echo "    git cherry-pick $c"; done
  echo "    git push origin promo/$RAMA"
  echo "    ~/scripts/abrir_pr.sh \"$TITULO\" promo/$RAMA"
  exit 2
fi

verde "La rama esta al dia: solo toca lo que tus commits tocaron."
git diff --stat origin/main "$REF" | sed 's/^/    /'

if [ -n "$CUERPO_FILE" ] && [ -r "$CUERPO_FILE" ]; then
  PR_CUERPO=$(cat "$CUERPO_FILE")
else
  PR_CUERPO=$(git log --format="## %s%n%n%b" origin/main.."$REF")
fi
PR_CUERPO="$PR_CUERPO

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
export PR_CUERPO

git rev-parse --verify -q "origin/$RAMA" >/dev/null 2>&1 || {
  echo "Subiendo la rama a origin..."; git push -q origin "$RAMA:$RAMA"; }

RES=$(python3 -c '
import json, os, sys, urllib.request, urllib.error
titulo, rama, repo, token = sys.argv[1:5]
dueno = repo.split("/")[0]
cab = {"Authorization": "token " + token, "Accept": "application/vnd.github+json"}
data = json.dumps({"title": titulo, "head": rama, "base": "main",
                   "body": os.environ.get("PR_CUERPO", "")}).encode()
try:
    r = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://api.github.com/repos/%s/pulls" % repo, data=data, headers=cab)))
    print("%s|%s" % (r["number"], r["html_url"]))
except urllib.error.HTTPError as e:
    d = e.read().decode()
    if "already exist" in d:
        q = "https://api.github.com/repos/%s/pulls?state=open&head=%s:%s" % (repo, dueno, rama)
        prs = json.load(urllib.request.urlopen(urllib.request.Request(q, headers=cab)))
        if prs:
            print("%s|%s  (ya existia)" % (prs[0]["number"], prs[0]["html_url"])); sys.exit(0)
    print("ERROR %s %s" % (e.code, d[:300]), file=sys.stderr); sys.exit(1)
' "$TITULO" "$RAMA" "$REPO" "$TOKEN")

verde "PR #${RES%%|*}"
echo "    ${RES##*|}"
echo
echo "El merge lo hace Mery o Fernando: main esta protegida y exige revision."
