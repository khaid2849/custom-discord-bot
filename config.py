import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Bot configuration settings"""
    
    # Discord Bot Token
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    
    # Bot Settings
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
    BOT_STATUS = os.getenv('BOT_STATUS', 'Listening to commands!')
    
    # Channel IDs (optional - add your specific channel IDs here)
    ANNOUNCEMENT_CHANNEL_ID = None  # Replace with your announcement channel ID
    LOG_CHANNEL_ID = None  # Replace with your log channel ID
    
    # Role IDs (optional - add your specific role IDs here)
    ADMIN_ROLE_ID = None  # Replace with your admin role ID
    MOD_ROLE_ID = None  # Replace with your moderator role ID
    
    # Bot Settings
    DELETE_COMMAND_MESSAGES = True  # Whether to delete command messages
    DEFAULT_EMBED_COLOR = 0x7289DA  # Discord blurple
    
    # Cooldowns (in seconds)
    DEFAULT_COOLDOWN = 3
    ANNOUNCEMENT_COOLDOWN = 30
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.DISCORD_TOKEN:
            raise ValueError("Discord token not found! Please set DISCORD_TOKEN in .env file")
        return True