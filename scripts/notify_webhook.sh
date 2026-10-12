#!/usr/bin/env bash
# Posts a message to the Discord webhook configured as HEALTH_WEBHOOK_URL in .env.
# Usage: notify_webhook.sh "<title>" "<body>" "<color>"
#   color: decimal Discord embed color (optional, defaults to gray)
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"

TITLE="${1:-Custom Discord Bot}"
BODY="${2:-}"
COLOR="${3:-8421504}"

if [ ! -f "$ENV_FILE" ]; then
    echo "notify_webhook.sh: no .env file found, cannot notify" >&2
    exit 1
fi

WEBHOOK_URL="$(grep -m1 '^HEALTH_WEBHOOK_URL=' "$ENV_FILE" | cut -d'=' -f2- || true)"

if [ -z "$WEBHOOK_URL" ]; then
    echo "notify_webhook.sh: HEALTH_WEBHOOK_URL not set in .env, skipping notification" >&2
    exit 0
fi

# Build JSON payload safely with python (handles escaping)
PAYLOAD="$(/usr/bin/python3 - "$TITLE" "$BODY" "$COLOR" <<'PYEOF'
import json, sys
title, body, color = sys.argv[1], sys.argv[2], int(sys.argv[3])
print(json.dumps({
    "embeds": [{
        "title": title,
        "description": body[:3900],
        "color": color,
    }]
}))
PYEOF
)"

curl -s -o /dev/null -w "%{http_code}" \
    -H "Content-Type: application/json" \
    -X POST \
    -d "$PAYLOAD" \
    "$WEBHOOK_URL" > /tmp/notify_webhook_status.txt || true
