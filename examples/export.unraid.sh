#!/bin/sh
# -----------------------------------------------------------------------------
# Paperless → Nextcloud Export (Unraid User Scripts version)
#
# This script runs inside Unraid using the "User Scripts" plugin.
# It calls the export script inside the Paperless-ngx container
# and pushes documents into Nextcloud via WebDAV.
#
# HOW TO USE:
# 1. Copy this file into:
#      /boot/config/plugins/user.scripts/scripts/paperless-export/
# 2. Make sure you have created a `.env` file based on `.env.example`
#    in the repo, with your PAPERLESS/Nextcloud settings filled in.
# 3. Adjust ENVFILE path below if needed.
# 4. Schedule it to run every 10 minutes in the User Scripts plugin.
# -----------------------------------------------------------------------------

set -e

# --- paths ---
ENVFILE="/mnt/user/appdata/paperless-ngx/tag-export/.env"
LOG="/mnt/user/appdata/paperless-ngx/tag-export/export.log"
LOCK="/tmp/paperless-export.lock"

# --- load secrets/vars from .env ---
. "$ENVFILE"

# Defaults (can be overridden in .env)
CONTAINER="${CONTAINER:-paperless-ngx}"
ROUTING="${ROUTING:-/state/routing.json}"

# --- helper: timestamp ---
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

# --- sanity checks ---
[ -n "$PAPERLESS_URL" ] || { logger -t paperless-export "missing PAPERLESS_URL"; exit 2; }
[ -n "$PAPERLESS_TOKEN" ] || { logger -t paperless-export "missing PAPERLESS_TOKEN"; exit 2; }
[ -n "$BASE_NC_URL" ] || { logger -t paperless-export "missing BASE_NC_URL"; exit 2; }
[ -n "$NC_USER" ] || { logger -t paperless-export "missing NC_USER"; exit 2; }
[ -n "$NC_PASS" ] || { logger -t paperless-export "missing NC_PASS"; exit 2; }

# --- run export (inside container) ---
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
