#!/usr/bin/env bash
set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
LOG_DIR=${AMUNET_MONITOR_LOG_DIR:-$ROOT_DIR/logs}
mkdir -p "$LOG_DIR" 2>/dev/null || true

errors=0
now=$(date -Is)

log() {
  echo "$now $*"
}

fail() {
  errors=$((errors + 1))
  log "ERROR $*"
}

check_container() {
  local name="$1"
  if ! docker inspect "$name" >/dev/null 2>&1; then
    fail "container_missing name=$name"
    return
  fi
  local state
  state=$(docker inspect -f '{{.State.Status}}' "$name" 2>/dev/null || echo unknown)
  if [ "$state" != "running" ]; then
    fail "container_not_running name=$name state=$state"
    return
  fi
  local health
  health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$name" 2>/dev/null || echo unknown)
  if [ "$health" != "healthy" ] && [ "$health" != "none" ]; then
    fail "container_unhealthy name=$name health=$health"
  fi
}

check_odoo_health() {
  local container="$1"
  local label="$2"
  if docker exec "$container" curl -sf http://localhost:8069/web/health >/dev/null 2>&1; then
    log "OK health label=$label container=$container"
  else
    fail "health_failed label=$label container=$container"
  fi
}

check_disk() {
  local path="${1:-/opt/odoo}"
  local threshold="${2:-85}"
  local used
  used=$(df -P "$path" | awk 'NR == 2 {gsub(/%/, "", $5); print $5}')
  if [ -n "$used" ] && [ "$used" -ge "$threshold" ]; then
    fail "disk_high path=$path used=${used}% threshold=${threshold}%"
  else
    log "OK disk path=$path used=${used}%"
  fi
}

check_container odoo-production
check_container odoo-production-db
check_container odoo-staging
check_container odoo-staging-db
check_odoo_health odoo-production production
check_odoo_health odoo-staging staging
check_disk /opt/odoo 85

if [ "$errors" -gt 0 ]; then
  log "SUMMARY status=fail errors=$errors"
  exit 1
fi

log "SUMMARY status=ok"
