# Discord Bot Project

A simple Discord bot built with discord.py that can make announcements and perform various utility functions.

## Features

- **Announcement System**: Make announcements with formatted embeds
- **Music Player**: Play music from YouTube with queue system
- **Basic Commands**: Ping, echo, server info, user info
- **Utility Commands**: Roll dice, create polls, clear messages
- **Slash Commands**: Modern Discord slash command support
- **Modular Design**: Uses cogs for organized command groups

## Prerequisites

- Python 3.8 or higher
- Discord account
- Discord server where you have admin permissions
- FFmpeg (for music functionality)

## Installation

1. Clone this repository or download the files
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a Discord application and bot:

   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to the Bot section and create a bot
   - Copy the bot token

4. Configure the bot:

   - Rename `.env.example` to `.env` (or create a new `.env` file)
   - Add your bot token to the `.env` file:
     ```
     DISCORD_TOKEN=your_bot_token_here
     ```

5. Invite the bot to your server:
   - In the Developer Portal, go to OAuth2 → URL Generator
   - Select `bot` and `applications.commands` scopes
   - Select necessary permissions (Send Messages, Read Message History, etc.)
   - Use the generated URL to invite the bot

## Usage

Run the bot:

```bash
python bot.py
```

## Available Commands

### Text Commands (prefix: `!`)

- `!announce <message>` - Make an announcement
- `!ping` - Check bot latency
- `!echo <message>` - Repeat a message
- `!serverinfo` - Get server information
- `!userinfo [@user]` - Get user information
- `!roll [NdN]` - Roll dice (e.g., 2d6)
- `!choose <option1> <option2> ...` - Choose between options
- `!poll <question>` - Create a yes/no poll
- `!avatar [@user]` - Get user's avatar
- `!clear <amount>` - Clear messages (requires permissions)
- `!help` - Show all commands

### Music Commands (prefix: `!`)

- `!play <song/URL>` - Play music from YouTube
- `!pause` - Pause current song
- `!resume` - Resume playback
- `!skip` - Skip current song
- `!stop` - Stop music and clear queue
- `!queue` - Show music queue
- `!nowplaying` - Show current song
- `!volume <0-100>` - Set volume
- `!join` - Join voice channel
- `!leave` - Leave voice channel

### Slash Commands

- `/hello` - Say hello
- `/say <message>` - Make the bot say something
- `/announce_slash <message> [channel]` - Announce with channel selection

## Project Structure

```
discord-bot/
├── .env                 # Environment variables
├── .gitignore          # Git ignore file
├── requirements.txt    # Dependencies
├── config.py          # Configuration
├── bot.py             # Main bot file
├── cogs/              # Command modules
│   └── general.py     # General commands
└── README.md          # This file
```

## Customization

- Edit `config.py` to change bot settings
- Add new commands in `bot.py` or create new cogs
- Modify embed colors and formatting in the command functions

## Security

- Never share your bot token
- Keep `.env` in `.gitignore`
- Use environment variables for sensitive data

## Troubleshooting

- **Bot not responding**: Check if MESSAGE_CONTENT intent is enabled
- **Slash commands not showing**: Wait a few minutes or restart Discord
- **Permission errors**: Ensure bot has proper permissions in the server
- **No audio when playing music**: Ensure FFmpeg is installed and in PATH
- **Music commands not working**: Install with `pip install discord.py[voice]`

## License

This project is open source and available for educational purposes.
