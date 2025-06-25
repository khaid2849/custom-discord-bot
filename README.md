# Discord Music Bot

A feature-rich Discord bot with music playback capabilities and comprehensive logging system.

## Features

- 🎵 **Music Playback**: Play music from YouTube with queue management
- 📋 **Queue System**: Add songs to queue, skip, pause, resume
- 🔊 **Voice Channel Management**: Auto-join/leave, volume control
- 📊 **Comprehensive Logging**: Track all bot activities and user interactions
- ⚙️ **Slash Commands**: Modern Discord slash command support
- 🛡️ **Error Handling**: Robust error handling and recovery

## Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd custom-discord-bot
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   Create a `.env` file:

   ```env
   DISCORD_TOKEN=your_bot_token_here
   COMMAND_PREFIX=!
   BOT_STATUS=Listening to music!
   ```

5. **Run the bot**
   ```bash
   python bot.py
   ```

## Commands

### Music Commands

- `!play <song name or URL>` - Play music from YouTube
- `!pause` - Pause the current song
- `!resume` - Resume the paused song
- `!skip` - Skip the current song
- `!stop` - Stop music and clear queue
- `!queue` - Show the music queue
- `!volume <0-100>` - Change volume
- `!join` - Join your voice channel
- `!leave` - Leave voice channel

### General Commands

- `!ping` - Check bot latency
- `!serverinfo` - Show server information
- `!announce <message>` - Make an announcement
- `!logs <lines>` - View recent logs (Admin only)

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

Edit `config.py` to customize bot settings:

```python
class Config:
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
    BOT_STATUS = os.getenv('BOT_STATUS', 'Listening to commands!')
    # ... other settings
```

## Project Structure

```
custom-discord-bot/
├── bot.py              # Main bot file
├── config.py           # Configuration settings
├── logger.py           # Logging system
├── log_viewer.py       # Log viewing utility
├── requirements.txt    # Python dependencies
├── cogs/              # Command modules
│   ├── music.py       # Music functionality
│   └── general.py     # General commands
└── logs/              # Log files (created automatically)
    ├── bot.log        # Main log
    ├── music.log      # Music activities
    └── errors.log     # Error log
```

## Requirements

- Python 3.8+
- discord.py 2.3+
- yt-dlp for YouTube downloads
- FFmpeg for audio processing

## Troubleshooting

### Common Issues

1. **Bot not responding to commands**

   - Check if the bot has necessary permissions
   - Verify the command prefix in your `.env` file
   - Check logs: `python log_viewer.py errors`

2. **Music not playing**

   - Ensure FFmpeg is installed and in PATH
   - Check voice channel permissions
   - View music logs: `python log_viewer.py music`

3. **Import errors**
   - Verify all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility

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

This project is licensed under the MIT License.

## Support

For support, check the logs first:

```bash
python log_viewer.py --stats
python log_viewer.py errors
```

If issues persist, create an issue with relevant log entries.
