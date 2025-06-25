import logging
import logging.handlers
import os
import json
import queue
import threading

from datetime import datetime

class AsyncLogHandler(logging.Handler):
    """Non-blocking log handler that uses a background thread"""
    
    def __init__(self, handler):
        super().__init__()
        self.handler = handler
        self.queue = queue.Queue()
        self.worker = threading.Thread(target=self._worker, daemon=True)
        self.worker.start()
    
    def _worker(self):
        """Background worker to process log records"""
        while True:
            try:
                record = self.queue.get()
                if record is None:
                    break
                self.handler.emit(record)
                self.queue.task_done()
            except Exception:
                pass
    
    def emit(self, record):
        """Emit a log record (non-blocking)"""
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            pass


class BotLogger:
    """Custom logger for Discord bot with non-blocking structured logging"""
    
    def __init__(self, name="DiscordBot", log_level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        if not self.logger.handlers:
            self.setup_handlers()
    
    def setup_handlers(self):
        """Setup file and console handlers with formatters"""
        
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/bot.log',
            maxBytes=10*1024*1024,
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        
        error_handler = logging.handlers.RotatingFileHandler(
            'logs/errors.log',
            maxBytes=5*1024*1024,
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        
        music_handler = logging.handlers.RotatingFileHandler(
            'logs/music.log',
            maxBytes=5*1024*1024,
            backupCount=3
        )
        music_handler.setLevel(logging.DEBUG)
        music_handler.setFormatter(file_format)
        
        music_filter = logging.Filter('DiscordBot.Music')
        music_handler.addFilter(music_filter)
        
        async_file_handler = AsyncLogHandler(file_handler)
        async_error_handler = AsyncLogHandler(error_handler)
        async_music_handler = AsyncLogHandler(music_handler)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(async_file_handler)
        self.logger.addHandler(async_error_handler)
        self.logger.addHandler(async_music_handler)
    
    def get_logger(self, module_name=None):
        """Get logger instance for specific module"""
        if module_name:
            return logging.getLogger(f"DiscordBot.{module_name}")
        return self.logger
    
    def log_command_usage(self, ctx, command_name, success=True, error=None):
        """Log command usage with structured data (non-blocking)"""
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
            'timestamp': datetime.now(datetime.UTC).isoformat()
        }
        
        if error:
            log_data['error'] = str(error)
            logger.error(f"Command failed: {json.dumps(log_data, separators=(',', ':'))}")
        else:
            logger.info(f"Command executed: {json.dumps(log_data, separators=(',', ':'))}")
    
    def log_music_activity(self, ctx, action, song_info=None, error=None):
        """Log music-related activities (non-blocking)"""
        logger = self.get_logger("Music")
        
        log_data = {
            'action': action,
            'user': str(ctx.author),
            'user_id': ctx.author.id,
            'guild': str(ctx.guild),
            'guild_id': ctx.guild.id,
            'voice_channel': str(ctx.author.voice.channel) if ctx.author.voice else None,
            'timestamp': datetime.now(datetime.UTC).isoformat()
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
            logger.error(f"Music error: {json.dumps(log_data, separators=(',', ':'))}")
        else:
            logger.info(f"Music activity: {json.dumps(log_data, separators=(',', ':'))}")
    
    def log_voice_event(self, member, before, after, event_type):
        """Log voice channel events (non-blocking)"""
        logger = self.get_logger("Voice")
        
        log_data = {
            'event_type': event_type,
            'user': str(member),
            'user_id': member.id,
            'guild': str(member.guild),
            'guild_id': member.guild.id,
            'before_channel': str(before.channel) if before.channel else None,
            'after_channel': str(after.channel) if after.channel else None,
            'timestamp': datetime.now(datetime.UTC).isoformat()
        }
        
        logger.info(f"Voice event: {json.dumps(log_data, separators=(',', ':'))}")
    
    def log_bot_event(self, event_type, details=None):
        """Log general bot events"""
        logger = self.get_logger("Bot")
        
        log_data = {
            'event_type': event_type,
            'timestamp': datetime.now(datetime.UTC).isoformat()
        }
        
        if details:
            log_data['details'] = details
        
        logger.info(f"Bot event: {json.dumps(log_data, indent=2)}")


bot_logger = BotLogger()

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