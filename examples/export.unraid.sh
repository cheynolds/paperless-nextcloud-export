#!/bin/sh
set -e

# --- paths ---
ENVFILE="/mnt/user/appdata/paperless-ngx/tag-export/.env"
LOG="/mnt/user/appdata/paperless-ngx/tag-export/export.log"
LOCK="/tmp/paperless-export.lock"

# --- load secrets/vars ---
# .env should define at least:
#   PAPERLESS_URL=...
#   PAPERLESS_TOKEN=...
#   BASE_NC_URL=...
#   NC_USER=...
#   NC_PASS=...
# Optional:
#   CONTAINER=paperless-ngx
#   ROUTING=/state/routing.json
. "$ENVFILE"

CONTAINER="${CONTAINER:-paperless-ngx}"
ROUTING="${ROUTING:-/state/routing.json}"

# --- tiny helpers ---
TS() { date -Is; }

# --- log rotation (5 MiB) ---
if [ -f "$LOG" ]; then
  SIZE=$(wc -c < "$LOG")
  [ "$SIZE" -gt 5242880 ] && mv "$LOG" "${LOG}.$(date +%Y%m%d%H%M%S)"
fi

# --- prevent overlapping runs ---
if ! mkdir "$LOCK" 2>/dev/null; then
  logger -t paperless-export "skip: previous run still active"
  exit 0
fi
trap 'rmdir "$LOCK"' EXIT

# --- basic sanity checks ---
[ -n "$PAPERLESS_URL" ] || { logger -t paperless-export "missing PAPERLESS_URL"; exit 2; }
[ -n "$PAPERLESS_TOKEN" ] || { logger -t paperless-export "missing PAPERLESS_TOKEN"; exit 2; }
[ -n "$BASE_NC_URL" ] || { logger -t paperless-export "missing BASE_NC_URL"; exit 2; }
[ -n "$NC_USER" ] || { logger -t paperless-export "missing NC_USER"; exit 2; }
[ -n "$NC_PASS" ] || { logger -t paperless-export "missing NC_PASS"; exit 2; }

# --- run export (no -t/-it) ---
logger -t paperless-export "run started"
{
  echo "[$(TS)] BEGIN"
  docker exec "$CONTAINER" sh -lc "
    python3 /scripts/export_tag_to_nextcloud.py \
      --paperless \"$PAPERLESS_URL\" \
      --token \"$PAPERLESS_TOKEN\" \
      --base-nc-url \"$BASE_NC_URL\" \
      --nc-user \"$NC_USER\" \
      --nc-pass \"$NC_PASS\" \
      --routing \"$ROUTING\"
  "
  echo "[$(TS)] END"
} >> "$LOG" 2>&1
RC=$?
logger -t paperless-export "run finished rc=$RC"
exit $RC
