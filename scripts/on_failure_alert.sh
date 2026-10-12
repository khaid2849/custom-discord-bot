#!/usr/bin/env bash
# Triggered by systemd's OnFailure= when custom-discord-bot.service gives up
# retrying (StartLimitBurst exceeded). Classifies the failure, attempts one
# safe recovery pass for library-version issues, retries once, and always
# notifies via Discord webhook (rate-limited to avoid spam on a persistent
# problem like a bad token).
set -uo pipefail

# Project root is the parent of this scripts/ directory; the bot runs as its owner
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BOT_USER="$(stat -c %U "$PROJECT_DIR")"
VENV_PIP="$PROJECT_DIR/venv/bin/python3 -m pip"
SERVICE="custom-discord-bot.service"
STATE_DIR="$PROJECT_DIR/state"
STATE_FILE="$STATE_DIR/last_failure_alert"
COOLDOWN_SECONDS=1800
NOTIFY="$PROJECT_DIR/scripts/notify_webhook.sh"

mkdir -p "$STATE_DIR"
chown "$BOT_USER:$BOT_USER" "$STATE_DIR" 2>/dev/null || true

NOW="$(date +%s)"
LAST="$(cat "$STATE_FILE" 2>/dev/null || echo 0)"
ELAPSED=$((NOW - LAST))

RECENT_LOG="$(journalctl -u "$SERVICE" -n 60 --no-pager -o cat 2>/dev/null || true)"

if [ "$ELAPSED" -lt "$COOLDOWN_SECONDS" ]; then
    echo "on_failure_alert: within cooldown (${ELAPSED}s < ${COOLDOWN_SECONDS}s), skipping notify/retry"
    exit 0
fi

echo "$NOW" > "$STATE_FILE"
chown "$BOT_USER:$BOT_USER" "$STATE_FILE" 2>/dev/null || true

CLASSIFICATION="unknown"
ADVICE=""

if echo "$RECENT_LOG" | grep -qi "Improper token has been passed"; then
    CLASSIFICATION="invalid_token"
    ADVICE="The Discord token in .env is being rejected (401 Unauthorized). This needs a human: reset the token in the Discord Developer Portal (Bot > Reset Token), update DISCORD_TOKEN in .env, then run: sudo systemctl restart $SERVICE"
elif echo "$RECENT_LOG" | grep -qiE "E2EE/DAVE protocol required|davey library needed"; then
    CLASSIFICATION="dave_protocol"
    ADVICE="Attempting automatic fix: upgrading discord.py and davey."
    runuser -u "$BOT_USER" -- $VENV_PIP install --upgrade discord.py davey >/tmp/dep_upgrade.log 2>&1
elif echo "$RECENT_LOG" | grep -qiE "ModuleNotFoundError|ImportError"; then
    CLASSIFICATION="missing_dependency"
    ADVICE="Attempting automatic fix: reinstalling requirements.txt."
    runuser -u "$BOT_USER" -- $VENV_PIP install -r "$PROJECT_DIR/requirements.txt" >/tmp/dep_upgrade.log 2>&1
else
    ADVICE="Unrecognized crash pattern. See the log excerpt below and check: journalctl -u $SERVICE -n 100"
fi

# One recovery attempt regardless of classification (safe: reset-failed just
# clears the start-limit counter, start is a no-op if it's already running).
systemctl reset-failed "$SERVICE" 2>/dev/null || true
systemctl start "$SERVICE" 2>/dev/null || true
sleep 8
STATUS="$(systemctl is-active "$SERVICE" 2>/dev/null || echo unknown)"

if [ "$STATUS" = "active" ]; then
    TITLE="Bot recovered automatically ✅"
    COLOR=3066993
    BODY="Service $SERVICE had crash-looped (classification: $CLASSIFICATION) but is running again after an automatic retry.

$ADVICE"
else
    TITLE="Bot is DOWN — needs attention ❌"
    COLOR=15158332
    BODY="Service $SERVICE stopped retrying after repeated failures (classification: $CLASSIFICATION) and did NOT recover automatically.

$ADVICE

Last log lines:
\`\`\`
$(echo "$RECENT_LOG" | tail -15)
\`\`\`"
fi

"$NOTIFY" "$TITLE" "$BODY" "$COLOR" || true
