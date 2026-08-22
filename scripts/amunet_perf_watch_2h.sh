#!/usr/bin/env bash
set -euo pipefail

DURATION_SECONDS="${1:-7200}"
INTERVAL_SECONDS="${2:-60}"
STAMP="$(TZ=America/Mexico_City date +%Y%m%d_%H%M%S)"
OUTDIR="/opt/odoo/staging/logs/perf_watch_${STAMP}"
mkdir -p "$OUTDIR"

PROD_LOG="/var/log/nginx/odoo_production_timing.log"
STAGING_LOG="/var/log/nginx/odoo_staging_timing.log"
PROD_OFFSET=0
STAGING_OFFSET=0
[ -f "$PROD_LOG" ] && PROD_OFFSET="$(stat -c%s "$PROD_LOG")"
[ -f "$STAGING_LOG" ] && STAGING_OFFSET="$(stat -c%s "$STAGING_LOG")"

{
  echo "START_MX=$(TZ=America/Mexico_City date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "DURATION_SECONDS=$DURATION_SECONDS"
  echo "INTERVAL_SECONDS=$INTERVAL_SECONDS"
  echo "OUTDIR=$OUTDIR"
} | tee "$OUTDIR/meta.log"

END_AT=$((SECONDS + DURATION_SECONDS))
while [ "$SECONDS" -lt "$END_AT" ]; do
  {
    echo "--- $(TZ=America/Mexico_City date '+%Y-%m-%d %H:%M:%S %Z') ---"
    uptime
    free -h | sed -n '1,2p'
    docker ps --format 'container={{.Names}} status={{.Status}}'
    for host in fc.amunet.com.mx stagingfc.amunet.com.mx; do
      curl -k -sS -o /dev/null -w "health host=$host status=%{http_code} time=%{time_total}\n" \
        --resolve "${host}:443:127.0.0.1" "https://${host}/web/health" || true
    done
    docker stats --no-stream --format 'stats container={{.Name}} cpu={{.CPUPerc}} mem={{.MemUsage}}' \
      odoo-production odoo-staging odoo-production-db odoo-staging-db 2>/dev/null || true
    ps -eo pid,etime,pcpu,pmem,cmd | grep -E 'docker compose|docker run .*odoo|odoo .* -u |--stop-after-init|build web-|up -d|force-recreate' | grep -v grep | sed -E 's/(PASSWORD=)[^ ]+/\1***MASKED***/g; s/(--db_password )[A-Za-z0-9_*.:-]+/\1***MASKED***/g' || true
  } >> "$OUTDIR/snapshots.log"
  sleep "$INTERVAL_SECONDS"
done

[ -f "$PROD_LOG" ] && tail -c +"$((PROD_OFFSET + 1))" "$PROD_LOG" > "$OUTDIR/nginx_production_window.log" || true
[ -f "$STAGING_LOG" ] && tail -c +"$((STAGING_OFFSET + 1))" "$STAGING_LOG" > "$OUTDIR/nginx_staging_window.log" || true
docker logs --since "${DURATION_SECONDS}s" odoo-production 2>&1 | grep 'AMUNET_SIGNATURE_' > "$OUTDIR/signature_production.log" || true
docker logs --since "${DURATION_SECONDS}s" odoo-staging 2>&1 | grep 'AMUNET_SIGNATURE_' > "$OUTDIR/signature_staging.log" || true

{
  echo "END_MX=$(TZ=America/Mexico_City date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "OUTDIR=$OUTDIR"
  echo
  echo "== Health samples =="
  grep '^health ' "$OUTDIR/snapshots.log" | tail -20 || true
  echo
  echo "== Active deploy/build/update samples =="
  grep -E 'docker compose|docker run .*odoo|odoo .* -u |--stop-after-init|build web-|force-recreate' "$OUTDIR/snapshots.log" | tail -30 || true
  echo
  echo "== Production 5xx count =="
  awk '{for(i=1;i<=NF;i++) if($i ~ /^status=/){s=substr($i,8); if(s ~ /^5/) c[s]++}} END{if(length(c)==0) print "none"; else for(s in c) print s,c[s]}' "$OUTDIR/nginx_production_window.log"
  echo
  echo "== Staging 5xx count =="
  awk '{for(i=1;i<=NF;i++) if($i ~ /^status=/){s=substr($i,8); if(s ~ /^5/) c[s]++}} END{if(length(c)==0) print "none"; else for(s in c) print s,c[s]}' "$OUTDIR/nginx_staging_window.log"
  echo
  echo "== Production slow requests >= 3s =="
  awk '{
    rt=""; ut=""; st=""; uri="";
    for(i=1;i<=NF;i++){
      if($i ~ /^request_time=/) rt=substr($i,14);
      if($i ~ /^upstream_time=/) ut=substr($i,15);
      if($i ~ /^status=/) st=substr($i,8);
      if($i ~ /^uri=/) uri=substr($i,5);
    }
    gsub(/^"|"$/, "", uri);
    if(rt+0 >= 3 && uri !~ /^\/websocket/) print rt, ut, st, uri;
  }' "$OUTDIR/nginx_production_window.log" | sort -nr | head -30
  echo
  echo "== Staging slow requests >= 3s =="
  awk '{
    rt=""; ut=""; st=""; uri="";
    for(i=1;i<=NF;i++){
      if($i ~ /^request_time=/) rt=substr($i,14);
      if($i ~ /^upstream_time=/) ut=substr($i,15);
      if($i ~ /^status=/) st=substr($i,8);
      if($i ~ /^uri=/) uri=substr($i,5);
    }
    gsub(/^"|"$/, "", uri);
    if(rt+0 >= 3 && uri !~ /^\/websocket/) print rt, ut, st, uri;
  }' "$OUTDIR/nginx_staging_window.log" | sort -nr | head -30
  echo
  echo "== Signature production =="
  cat "$OUTDIR/signature_production.log" || true
  echo
  echo "== Signature staging =="
  cat "$OUTDIR/signature_staging.log" || true
} | tee "$OUTDIR/summary.log"
