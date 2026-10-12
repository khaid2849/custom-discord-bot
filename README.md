# Discord Music Bot

A self-hosted Discord bot that plays music from YouTube, shows song lyrics, and keeps detailed logs of everything it does.

## Features

- 🎵 **Music Playback**: Play music from YouTube by name or URL, with per-server queues
- 📋 **Queue System**: Add songs to the queue, skip, pause, resume, show what's playing
- 🎤 **Lyrics**: Look up lyrics for the current song (or any song) via [LRCLIB](https://lrclib.net), no API key needed
- 🔊 **Voice Channel Management**: Joins your channel on demand, leaves automatically when left alone
- 📊 **Comprehensive Logging**: Track all bot activities and user interactions
- ⚙️ **Slash Commands**: Modern Discord slash command support
- 🛡️ **Self-healing service**: Optional systemd setup with auto-restart, crash alerts and daily dependency updates ([SERVICE_SETUP.md](SERVICE_SETUP.md))

## Requirements

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) available in `PATH` (Ubuntu/Debian: `sudo apt install ffmpeg`, macOS: `brew install ffmpeg`)
- A Discord bot application (see below)

## Discord Bot Setup

1. Create an application at the [Discord Developer Portal](https://discord.com/developers/applications).
2. In **Bot**, click **Reset Token** and copy the token (you'll put it in `.env`).
3. In **Bot > Privileged Gateway Intents**, enable **Message Content Intent** (needed for `!` prefix commands).
4. In **OAuth2 > URL Generator**, select the scopes `bot` and `applications.commands`, then the permissions:
   Send Messages, Embed Links, Read Message History, Add Reactions, Manage Messages (for `!clear`), Connect, Speak.
   Open the generated URL to invite the bot to your server.

## Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/khaid2849/custom-discord-bot.git
   cd custom-discord-bot
   ```

2. **Create virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and set at least `DISCORD_TOKEN`:

   ```env
   DISCORD_TOKEN=your_bot_token_here
   COMMAND_PREFIX=!
   BOT_STATUS=Listening to music!
   ```

5. **Run the bot**

   ```bash
   python bot.py
   ```

   On startup the bot upgrades `yt-dlp` automatically, since YouTube changes often break older versions.

To keep the bot running in the background on a Linux server (auto-start on boot, restart on crash), see [SERVICE_SETUP.md](SERVICE_SETUP.md).

## Commands

### Music Commands

- `!play <song name or URL>` (`!p`) - Play music from YouTube, or add it to the queue
- `!pause` - Pause the current song
- `!resume` - Resume the paused song
- `!skip` (`!s`) - Skip the current song
- `!stop` - Stop music and clear the queue
- `!queue` (`!q`) - Show the music queue
- `!nowplaying` (`!np`) - Show the current song
- `!volume <0-100>` - Change volume
- `!join` - Join your voice channel
- `!leave` (`!dc`) - Leave the voice channel
- `!lyrics [song name]` (`!ly`) - Show lyrics of the current song, or search for a given song

### General Commands

- `!ping` - Check bot latency
- `!serverinfo` - Show server information
- `!userinfo [@member]` - Show information about a user
- `!avatar [@member]` - Show a user's avatar
- `!roll [NdM]` - Roll dice, e.g. `!roll 2d20`
- `!choose <a> <b> ...` - Pick one of several options
- `!poll <question>` - Create a yes/no poll
- `!clear [amount]` - Delete recent messages (requires Manage Messages)
- `!echo <message>` - Repeat a message
- `!announce <message>` - Make an announcement
- `!logs [lines]` - View recent logs (Administrator only)

### Slash Commands

- `/hello` - Say hello to the bot
- `/say <message>` - Make the bot say something
- `/announce_slash <message> [channel]` - Announce with slash command

## Logging System

The bot includes a comprehensive logging system that tracks:

### Log Files

- `logs/bot.log` - Main bot activities and command usage
- `logs/music.log` - Music-specific activities (play, queue, etc.)
- `logs/errors.log` - Error messages and exceptions

Logs include Discord usernames, user IDs and server names. They stay on your machine (`logs/` is git-ignored); keep that in mind before sharing them.

### Log Viewer

Use the included log viewer to monitor bot activities:

```bash
# View last 50 lines from main log
python log_viewer.py bot

# View last 100 lines from music log
python log_viewer.py music -n 100

# Watch for new log entries in real-time
python log_viewer.py bot --watch

# Show log statistics
python log_viewer.py --stats

# View all logs
python log_viewer.py all
```

### Logged Activities

- ✅ **Bot Startup/Shutdown**: Connection status, guild count
- ✅ **Command Usage**: All commands with user and context info
- ✅ **Music Activities**: Play, pause, skip, queue management
- ✅ **Voice Events**: Join/leave voice channels
- ✅ **Errors**: All errors with full stack traces
- ✅ **Guild Events**: Bot joining/leaving servers

### Log Format

Logs are stored in structured JSON format for easy parsing:

```json
{
  "command": "play",
  "user": "Username#1234",
  "user_id": 123456789,
  "guild": "Server Name",
  "guild_id": 987654321,
  "success": true,
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

## Configuration

Settings are read from `.env` (see `.env.example`):

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | Yes | Bot token from the Developer Portal |
| `COMMAND_PREFIX` | No | Prefix for text commands (default `!`) |
| `BOT_STATUS` | No | Text shown as the bot's activity |
| `HEALTH_WEBHOOK_URL` | No | Discord webhook for service alerts ([SERVICE_SETUP.md](SERVICE_SETUP.md)) |

Other defaults (cooldowns, embed color, ...) live in `config.py`.

## Project Structure

```
custom-discord-bot/
├── bot.py                 # Main bot file
├── config.py              # Configuration settings
├── logger.py              # Logging system
├── log_viewer.py          # Log viewing utility
├── requirements.txt       # Python dependencies
├── .env.example           # Template for your .env
├── cogs/                  # Command modules (every .py here is loaded automatically)
│   ├── music.py           # Music functionality
│   ├── lyrics.py          # Lyrics lookup
│   └── general.py         # General commands
├── scripts/               # Alert / healthcheck scripts used by the systemd units
├── custom-discord-bot*.service, *.timer   # systemd unit templates
└── logs/                  # Log files (created automatically)
```

To add your own commands, create `cogs/<name>.py` with an `async def setup(bot)` function; it is picked up on the next start.

## Troubleshooting

### Common Issues

1. **Bot not responding to commands**

   - Make sure **Message Content Intent** is enabled in the Developer Portal
   - Check if the bot has necessary permissions in the channel
   - Verify the command prefix in your `.env` file
   - Check logs: `python log_viewer.py errors`

2. **Music not playing**

   - Ensure FFmpeg is installed and in `PATH`
   - Check the bot has Connect and Speak permissions in the voice channel
   - Update yt-dlp (`pip install -U yt-dlp`); YouTube changes frequently break older versions
   - View music logs: `python log_viewer.py music`

3. **Import errors**
   - Verify all dependencies are installed: `pip install -r requirements.txt`
   - Check you are on Python 3.10 or newer

### Log Analysis

Use the logging system to debug issues:

```bash
# Check for recent errors
python log_viewer.py errors -n 20

# Monitor real-time activity
python log_viewer.py bot --watch

# Check specific command usage
grep "play" logs/bot.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add appropriate logging
5. Test thoroughly
6. Submit a pull request

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE).

## Support

For support, check the logs first:

```bash
python log_viewer.py --stats
python log_viewer.py errors
```

If issues persist, [open an issue](https://github.com/khaid2849/custom-discord-bot/issues) with relevant log entries (remove user IDs or other personal data first).
