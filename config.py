import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Bot configuration settings"""
    
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
    BOT_STATUS = os.getenv('BOT_STATUS', 'Listening to commands!')
    
    ANNOUNCEMENT_CHANNEL_ID = None
    LOG_CHANNEL_ID = None
    
    ADMIN_ROLE_ID = None
    MOD_ROLE_ID = None
    
    DELETE_COMMAND_MESSAGES = True
    DEFAULT_EMBED_COLOR = 0x7289DA
    
    DEFAULT_COOLDOWN = 3
    ANNOUNCEMENT_COOLDOWN = 30
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.DISCORD_TOKEN:
            raise ValueError("Discord token not found! Please set DISCORD_TOKEN in .env file")
        return True