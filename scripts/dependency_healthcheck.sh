#!/usr/bin/env bash
# Daily proactive maintenance: keeps the Discord-protocol-sensitive
# dependencies (discord.py, davey, yt-dlp) up to date so version-gap issues
# (like the DAVE E2EE requirement, or YouTube extractor breakage) are fixed
# before they cause a failure, not after. Also does a safety-net check that
# the service is actually up. Runs as root (systemd oneshot); pip/venv work
# is done as the project owner to keep file ownership correct.
set -uo pipefail

# Project root is the parent of this scripts/ directory; the bot runs as its owner
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BOT_USER="$(stat -c %U "$PROJECT_DIR")"
VENV_PY="$PROJECT_DIR/venv/bin/python3"
SERVICE="custom-discord-bot.service"
NOTIFY="$PROJECT_DIR/scripts/notify_webhook.sh"
LOG_FILE="$PROJECT_DIR/logs/dependency_healthcheck.log"
PACKAGES=("discord.py" "davey" "yt-dlp")

mkdir -p "$PROJECT_DIR/logs"
touch "$LOG_FILE"
chown "$BOT_USER:$BOT_USER" "$LOG_FILE" 2>/dev/null || true
log() { echo "$(date -Iseconds) | $*" >> "$LOG_FILE"; }

get_version() {
    runuser -u "$BOT_USER" -- "$VENV_PY" -m pip show "$1" 2>/dev/null | grep -m1 '^Version:' | awk '{print $2}'
}

UPGRADED=()
BEFORE_VERSIONS=()
for pkg in "${PACKAGES[@]}"; do
    BEFORE_VERSIONS+=("$pkg=$(get_version "$pkg")")
done

log "Checking for updates: ${PACKAGES[*]}"
UPGRADE_OUTPUT="$(runuser -u "$BOT_USER" -- "$VENV_PY" -m pip install --upgrade "${PACKAGES[@]}" 2>&1)"
UPGRADE_STATUS=$?
log "pip upgrade exit=$UPGRADE_STATUS"

AFTER_VERSIONS=()
CHANGED=false
for i in "${!PACKAGES[@]}"; do
    pkg="${PACKAGES[$i]}"
    new_v="$(get_version "$pkg")"
    AFTER_VERSIONS+=("$pkg=$new_v")
    old_v="${BEFORE_VERSIONS[$i]#*=}"
    if [ "$old_v" != "$new_v" ]; then
        CHANGED=true
        UPGRADED+=("$pkg: $old_v -> $new_v")
    fi
done

RESTARTED=false
if [ "$CHANGED" = true ]; then
    log "Versions changed, restarting $SERVICE"
    systemctl restart "$SERVICE"
    RESTARTED=true
    sleep 8
fi

STATUS="$(systemctl is-active "$SERVICE" 2>/dev/null || echo unknown)"

# Safety net: even if nothing needed upgrading, make sure the service is up.
if [ "$STATUS" != "active" ]; then
    log "Service not active ($STATUS), attempting recovery"
    systemctl reset-failed "$SERVICE" 2>/dev/null || true
    systemctl start "$SERVICE" 2>/dev/null || true
    sleep 8
    STATUS="$(systemctl is-active "$SERVICE" 2>/dev/null || echo unknown)"
fi

if [ "$UPGRADE_STATUS" -ne 0 ]; then
    "$NOTIFY" "Daily dependency check: upgrade FAILED ⚠️" \
        "pip install --upgrade ${PACKAGES[*]} failed (exit $UPGRADE_STATUS). Service status: $STATUS.

\`\`\`
$(echo "$UPGRADE_OUTPUT" | tail -20)
\`\`\`" 15158332
elif [ "$CHANGED" = true ]; then
    "$NOTIFY" "Bot dependencies auto-updated ✅" \
        "$(printf '%s\n' "${UPGRADED[@]}")

Service restarted, status: $STATUS." 3066993
elif [ "$STATUS" != "active" ]; then
    "$NOTIFY" "Bot service is DOWN ❌" \
        "No dependency updates were needed, but $SERVICE is not active (status: $STATUS) and did not recover automatically. Check: journalctl -u $SERVICE -n 50" 15158332
else
    log "Nothing to do, service healthy. Versions: ${AFTER_VERSIONS[*]}"
fi
