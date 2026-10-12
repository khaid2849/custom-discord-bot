# Setting up Discord Bot as Ubuntu Service

This guide will help you set up your Discord bot to run as a systemd service on Ubuntu.

## Prerequisites

1. Follow the Quick Start in [README.md](README.md) so the project has a `venv/`
   with all dependencies installed (the service runs `venv/bin/python3`).

2. Ensure your `.env` file is properly configured with your Discord token.

## Installation Steps

### 1. Install the unit files

The unit files in this repo are templates: `/path/to/custom-discord-bot` and
`YOUR_USER` are placeholders. Run this from the project directory, as the user
that should run the bot, to fill them in and copy them to systemd:

```bash
for unit in custom-discord-bot*.service custom-discord-bot-healthcheck.timer; do
    sed -e "s|/path/to/custom-discord-bot|$PWD|g" -e "s|YOUR_USER|$USER|g" "$unit" \
        | sudo tee "/etc/systemd/system/$unit" > /dev/null
done
```

To tweak the installed service afterwards:
```bash
sudo nano /etc/systemd/system/custom-discord-bot.service
```

### 3. Reload systemd daemon

```bash
sudo systemctl daemon-reload
```

### 4. Enable the service (to start on boot)

```bash
sudo systemctl enable custom-discord-bot.service
```

### 5. Start the service

```bash
sudo systemctl start custom-discord-bot.service
```

## Managing the Service

### Check service status
```bash
sudo systemctl status custom-discord-bot.service
```

### View logs
```bash
# View recent logs
sudo journalctl -u custom-discord-bot.service -n 50

# Follow logs in real-time
sudo journalctl -u custom-discord-bot.service -f

# View logs since boot
sudo journalctl -u custom-discord-bot.service -b
```

### Stop the service
```bash
sudo systemctl stop custom-discord-bot.service
```

### Restart the service
```bash
sudo systemctl restart custom-discord-bot.service
```

### Disable auto-start on boot
```bash
sudo systemctl disable custom-discord-bot.service
```

## Troubleshooting

1. **Service fails to start**: Check logs with `sudo journalctl -u custom-discord-bot.service -n 100`
2. **Permission errors**: Ensure the user specified in the service file has access to the project directory
3. **Python not found**: Update the `ExecStart` path with the correct Python 3 path (use `which python3`)
4. **Environment variables not loading**: The service uses the `.env` file in the working directory. Ensure it exists and is readable.

## Notes

- The service will automatically restart if the bot crashes (with a 10-second delay)
- Logs are sent to systemd journal and can be viewed with `journalctl`
- The service runs as the specified user (not root) for security

## Auto-monitoring and self-healing

The service is configured to give up retrying after 6 failures within 5 minutes
(`StartLimitIntervalSec`/`StartLimitBurst` in `custom-discord-bot.service`) rather
than crash-loop forever silently. When that happens, `OnFailure=` triggers an
alert unit; a separate daily timer also proactively keeps Discord/YouTube-facing
dependencies (`discord.py`, `davey`, `yt-dlp`) up to date, since those are the
packages most likely to break as Discord/YouTube change their protocols
(e.g. the DAVE E2EE voice requirement).

Both mechanisms notify a Discord channel via webhook. Set the webhook URL once
in `.env`:
```
HEALTH_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Install

The unit files are already installed by step 1 of the installation above; just
reload systemd and enable the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl restart custom-discord-bot.service
sudo systemctl enable --now custom-discord-bot-healthcheck.timer
```

### What each piece does

- **`custom-discord-bot-alert.service`** (event-driven, via `OnFailure=`): fires
  only when the main service exhausts its restart budget. Classifies the crash
  from recent logs (bad token vs. missing DAVE library vs. missing dependency),
  attempts a safe fix for the ones it can (reinstalling/upgrading packages),
  retries the service once, and always notifies with the outcome. Rate-limited
  to one notification per 30 minutes so a persistent problem (like a bad token)
  doesn't spam the channel — you'll get one alert, then silence until you fix it
  or 30 minutes pass.
- **`custom-discord-bot-healthcheck.timer`** (daily, 04:15 local + up to 5 min
  jitter): checks for newer `discord.py`/`davey`/`yt-dlp` releases, upgrades and
  restarts the bot if any changed, and as a safety net also restarts the service
  if it's found not running. Silent when there's nothing to do; notifies only on
  an upgrade, a restart, or a failure it couldn't resolve.

### What this does NOT auto-fix

An invalid/revoked `DISCORD_TOKEN` needs a human: reset it in the
[Discord Developer Portal](https://discord.com/developers/applications) (Bot >
Reset Token), update `.env`, then `sudo systemctl restart custom-discord-bot.service`.
The alert will name this case explicitly when it's the cause.

### Manually run a check

```bash
sudo systemctl start custom-discord-bot-healthcheck.service   # dependency check now
./scripts/notify_webhook.sh "Test" "Webhook test message" 3066993   # from the project directory
```
