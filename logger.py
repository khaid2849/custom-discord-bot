import logging
import logging.handlers
import os
from datetime import datetime
import json


class BotLogger:
    """Custom logger for Discord bot with structured logging"""
    
    def __init__(self, name="DiscordBot", log_level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self.setup_handlers()
    
    def setup_handlers(self):
        """Setup file and console handlers with formatters"""
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/bot.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            'logs/errors.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        
        # Music activity handler
        music_handler = logging.handlers.RotatingFileHandler(
            'logs/music.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        music_handler.setLevel(logging.DEBUG)
        music_handler.setFormatter(file_format)
        
        # Add filter for music logger
        music_filter = logging.Filter('DiscordBot.Music')
        music_handler.addFilter(music_filter)
        
        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(music_handler)
    
    def get_logger(self, module_name=None):
        """Get logger instance for specific module"""
        if module_name:
            return logging.getLogger(f"DiscordBot.{module_name}")
        return self.logger
    
    def log_command_usage(self, ctx, command_name, success=True, error=None):
        """Log command usage with structured data"""
        logger = self.get_logger("Commands")
        
        log_data = {
            'command': command_name,
            'user': str(ctx.author),
            'user_id': ctx.author.id,
            'guild': str(ctx.guild) if ctx.guild else 'DM',
            'guild_id': ctx.guild.id if ctx.guild else None,
            'channel': str(ctx.channel),
            'channel_id': ctx.channel.id,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if error:
            log_data['error'] = str(error)
            logger.error(f"Command failed: {json.dumps(log_data, indent=2)}")
        else:
            logger.info(f"Command executed: {json.dumps(log_data, indent=2)}")
    
    def log_music_activity(self, ctx, action, song_info=None, error=None):
        """Log music-related activities"""
        logger = self.get_logger("Music")
        
        log_data = {
            'action': action,
            'user': str(ctx.author),
            'user_id': ctx.author.id,
            'guild': str(ctx.guild),
            'guild_id': ctx.guild.id,
            'voice_channel': str(ctx.author.voice.channel) if ctx.author.voice else None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if song_info:
            log_data['song'] = {
                'title': song_info.get('title', 'Unknown'),
                'url': song_info.get('url', ''),
                'duration': song_info.get('duration', 0),
                'channel': song_info.get('channel', 'Unknown')
            }
        
        if error:
            log_data['error'] = str(error)
            logger.error(f"Music error: {json.dumps(log_data, indent=2)}")
        else:
            logger.info(f"Music activity: {json.dumps(log_data, indent=2)}")
    
    def log_voice_event(self, member, before, after, event_type):
        """Log voice channel events"""
        logger = self.get_logger("Voice")
        
        log_data = {
            'event_type': event_type,
            'user': str(member),
            'user_id': member.id,
            'guild': str(member.guild),
            'guild_id': member.guild.id,
            'before_channel': str(before.channel) if before.channel else None,
            'after_channel': str(after.channel) if after.channel else None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Voice event: {json.dumps(log_data, indent=2)}")
    
    def log_bot_event(self, event_type, details=None):
        """Log general bot events"""
        logger = self.get_logger("Bot")
        
        log_data = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if details:
            log_data['details'] = details
        
        logger.info(f"Bot event: {json.dumps(log_data, indent=2)}")


# Global logger instance
bot_logger = BotLogger()

# Convenience functions
def get_logger(module_name=None):
    """Get logger for specific module"""
    return bot_logger.get_logger(module_name)

def log_command(ctx, command_name, success=True, error=None):
    """Log command usage"""
    bot_logger.log_command_usage(ctx, command_name, success, error)

def log_music(ctx, action, song_info=None, error=None):
    """Log music activity"""
    bot_logger.log_music_activity(ctx, action, song_info, error)

def log_voice(member, before, after, event_type):
    """Log voice events"""
    bot_logger.log_voice_event(member, before, after, event_type)

def log_bot(event_type, details=None):
    """Log bot events"""
    bot_logger.log_bot_event(event_type, details) 