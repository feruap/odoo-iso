#!/usr/bin/env bash
# aviso_area.sh <from> <to> <subject> <body> [parent_id]
set -e
FROM="$1"; TO="$2"; SUB="$3"; BODY="$4"; PARENT="${5:-}"
BASE=/home/agentia-odoo/inboxes
[ -d "$BASE/$TO/inbox" ] || { echo "ERROR area $TO no existe" >&2; exit 1; }
[ -d "$BASE/$FROM" ] || { echo "ERROR area $FROM no existe" >&2; exit 1; }

# Deriva el area de la SESION que ejecuta, no de lo que declara quien llama.
# Nunca falla: si no la puede determinar devuelve vacio y el script sigue igual.
#
# Dos vias, en orden: CLAUDE_CONFIG_DIR (lo tienen 11 de las 12 sesiones) y el
# nombre de la sesion de tmux, que es 'claude-<sesion>'. La sesion principal
# ('claude-web') no tiene la variable, de ahi la segunda via.
_amunet_sesion_a_area() {
  case "$1" in
    web|desarrollo|dev2|dev3) echo "desarrollo" ;;   # las de desarrollo comparten buzon
    "")                       echo "" ;;
    *)                        echo "$1" ;;
  esac
}
_amunet_area_real() {
  local cfg="${CLAUDE_CONFIG_DIR:-}" p=$PPID i base ses
  if [ -z "$cfg" ]; then
    for i in 1 2 3 4 5 6; do
      [ -r "/proc/$p/environ" ] || break
      cfg=$(tr '\0' '\n' < "/proc/$p/environ" 2>/dev/null | sed -n 's/^CLAUDE_CONFIG_DIR=//p' | head -1)
      [ -n "$cfg" ] && break
      p=$(awk '{print $4}' "/proc/$p/stat" 2>/dev/null) || break
      { [ -z "$p" ] || [ "$p" = "1" ]; } && break
    done
  fi
  if [ -n "$cfg" ]; then
    base=$(basename "$cfg")
    case "$base" in
      .claude)   _amunet_sesion_a_area "web"; return ;;
      .claude-*) _amunet_sesion_a_area "${base#.claude-}"; return ;;
    esac
  fi
  # segunda via: el nombre de la sesion de tmux
  ses=$(tmux display-message -p '#S' 2>/dev/null)
  case "$ses" in
    claude-*) _amunet_sesion_a_area "${ses#claude-}" ;;
    *)        echo "" ;;
  esac
}

# El remitente lo declara quien llama, asi que un agente puede firmar como otra
# area sin querer. Paso el 29-sep-2026: un reporte de Almacen PT llego firmado
# como Almacen MP y se le atribuyo a la persona equivocada.
# No se bloquea el envio -- eso dejaria a las 12 sesiones sin poder avisarse --,
# pero si la sesion real no coincide con lo declarado queda anotado en el
# mensaje y en la pantalla, para que la atribucion no se pierda.
AREA_REAL=$(_amunet_area_real)
DISCREPANCIA=""
if [ -n "$AREA_REAL" ] && [ "$AREA_REAL" != "$FROM" ]; then
  DISCREPANCIA="$AREA_REAL"
  echo "AVISO: lo mandas como '$FROM' pero esta sesion es '$AREA_REAL'." >&2
  echo "       Se envia igual, y queda anotado de donde salio." >&2
fi
TS=$(date -u +"%Y%m%dT%H%M%SZ"); ID="msg-${TS}-$$"
F="$BASE/$TO/inbox/${ID}.md"
{
 echo "---"; echo "id: $ID"; echo "from: $FROM"; echo "to: $TO"
 echo "subject: $SUB"; echo "created_at: $(date -Iseconds)"
 [ -n "$DISCREPANCIA" ] && echo "enviado_por_sesion: $DISCREPANCIA"
 [ -n "$PARENT" ] && echo "parent: $PARENT"
 echo "---"; echo; echo "$BODY"
 if [ -n "$DISCREPANCIA" ]; then
   echo
   echo "> Nota del sistema: este aviso se firmo como '$FROM' pero lo envio la"
   echo "> sesion de '$DISCREPANCIA'. Si hace falta responder, hazlo a '$DISCREPANCIA'."
 fi
} > "$F"; chmod 660 "$F"
# correo de cortesia al humano del area destino
declare -A EMAIL=( [almacen2]="almacen2@amunet.com.mx" [almacenmp]="almacen.mp@amunet.com.mx" [ensayo]="ensayo@amunet.com.mx" [rrhh]="rrhh@amunet.com.mx" [documentacion]="documentacion@amunet.com.mx" [calidad]="s.controldecalidad@amunet.com.mx" [pm]="desarrollo@amunet.com.mx" [desarrollo]="desarrollo@amunet.com.mx" [fernando]="fernando.ruiz@amunet.com.mx" )
TARGET="${EMAIL[$TO]}"
if [ -n "$TARGET" ]; then
  MSG="Hola: el agente del area '$FROM' te dejo un aviso en tu sesion de Claude.

Asunto: $SUB

Cuando entres a https://agentfc.amunet.com.mx tu asistente te lo va a mostrar
(o pidele: 'revisa tu buzon'). Tambien puedes contestarle desde ahi y tu agente
le respondera al de $FROM.

-- Agente Claude Amunet (aviso entre areas)"
  python3 /home/agentia-odoo/scripts/_send_mail.py --to "$TARGET" --subject "[Aviso entre areas] $SUB" --body "$MSG" >/dev/null 2>&1 || true
fi
echo "OK $ID"
