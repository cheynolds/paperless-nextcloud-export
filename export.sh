#!/bin/sh
set -e

# Load environment variables from .env
. ./.env

CONTAINER="${CONTAINER:-paperless-ngx}"
ROUTING="${ROUTING:-/state/routing.json}"

# Run export inside the Paperless container
docker exec "$CONTAINER" sh -lc "
  python3 /scripts/export_tag_to_nextcloud.py \
    --paperless \"$PAPERLESS_URL\" \
    --token \"$PAPERLESS_TOKEN\" \
    --base-nc-url \"$BASE_NC_URL\" \
    --nc-user \"$NC_USER\" \
    --nc-pass \"$NC_PASS\" \
    --routing \"$ROUTING\"
"
