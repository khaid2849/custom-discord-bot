import discord
import asyncio
import yt_dlp as youtube_dl
import re

from discord.ext import commands
from logger import get_logger, log_music, log_voice

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

logger = get_logger("Music")

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.channel = data.get('channel')
        self.view_count = data.get('view_count')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            
            if 'entries' in data:
                data = data['entries'][0]

            filename = data['url'] if stream else ytdl.prepare_filename(data)
            
            source = cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
            
            asyncio.create_task(cls._log_extraction_success(data.get('title', 'Unknown')))
            
            return source
            
        except Exception as e:
            asyncio.create_task(cls._log_extraction_error(url, str(e)))
            raise

    @staticmethod
    async def _log_extraction_success(title):
        """Async logging for successful extraction"""
        logger.debug(f"Successfully extracted and created source for: {title}")

    @staticmethod
    async def _log_extraction_error(url, error):
        """Async logging for extraction errors"""
        logger.error(f"Failed to extract info for URL {url}: {error}")

class Music(commands.Cog):
    """Music commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.music_queues = {}
        logger.info("Music cog initialized")
        
    def get_queue(self, ctx):
        """Get the music queue for a guild"""
        if ctx.guild.id not in self.music_queues:
            self.music_queues[ctx.guild.id] = []
        return self.music_queues[ctx.guild.id]
    
    async def play_next(self, ctx):
        """Play the next song in the queue"""
        queue = self.get_queue(ctx)
        
        if len(queue) > 0:
            next_song = queue.pop(0)
            
            try:
                player = await YTDLSource.from_url(next_song['url'], loop=self.bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next(ctx), self.bot.loop
                ))
                
                asyncio.create_task(self._log_and_announce_next(ctx, next_song, player))
                
            except Exception as e:
                asyncio.create_task(self._log_play_error(ctx, next_song, str(e)))
                await ctx.send(f"❌ Error playing song: {str(e)}")
                await self.play_next(ctx)  # Try next song

    async def _log_and_announce_next(self, ctx, song_info, player):
        """Async logging and announcement for next song"""
        logger.info(f"Playing next song: {song_info['title']} in {ctx.guild.name}")
        log_music(ctx, "play_next", song_info)
        
        # Send now playing message
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[{player.title}]({song_info['url']})",
            color=discord.Color.green()
        )
        if player.thumbnail:
            embed.set_thumbnail(url=player.thumbnail)
        embed.add_field(name="Duration", value=self.format_duration(player.duration), inline=True)
        embed.add_field(name="Requested by", value=song_info['requester'].mention, inline=True)
        
        await ctx.send(embed=embed)

    async def _log_play_error(self, ctx, song_info, error):
        """Async logging for play errors"""
        logger.error(f"Error playing next song: {error}")
        log_music(ctx, "play_next_error", song_info, error=error)
    
    def format_duration(self, duration):
        """Format duration from seconds to MM:SS"""
        if duration:
            minutes, seconds = divmod(duration, 60)
            return f"{int(minutes):02d}:{int(seconds):02d}"
        return "Unknown"
    
    async def search_youtube(self, query):
        """Search YouTube and return the first result"""
        loop = asyncio.get_event_loop()
        
        # Check if it's a URL
        url_pattern = re.compile(
            r'(https?://)?(www\.)?(youtube\.com/(watch\?v=|embed/|v/)|youtu\.be/|youtube\.com/playlist\?list=)'
        )
        
        search_query = query if url_pattern.match(query) else f"ytsearch:{query}"
        
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))
            
            if 'entries' in data and data['entries']:
                # Get first result
                video = data['entries'][0]
                result = {
                    'title': video.get('title', 'Unknown'),
                    'url': video.get('webpage_url', video.get('url')),
                    'duration': video.get('duration', 0),
                    'thumbnail': video.get('thumbnail'),
                    'channel': video.get('channel', 'Unknown')
                }
                # Log success asynchronously
                asyncio.create_task(self._log_search_success(result))
                return result
            elif 'title' in data:
                # Direct URL result
                result = {
                    'title': data.get('title', 'Unknown'),
                    'url': data.get('webpage_url', data.get('url')),
                    'duration': data.get('duration', 0),
                    'thumbnail': data.get('thumbnail'),
                    'channel': data.get('channel', 'Unknown')
                }
                asyncio.create_task(self._log_search_success(result))
                return result
        except Exception as e:
            asyncio.create_task(self._log_search_error(query, str(e)))
            return None

    async def _log_search_success(self, result):
        """Async logging for successful search"""
        logger.info(f"Found video: {result['title']} by {result['channel']}")

    async def _log_search_error(self, query, error):
        """Async logging for search errors"""
        logger.error(f"Search error for query '{query}': {error}")
    
    @commands.command(name='play', aliases=['p'], help='Play music from YouTube')
    async def play(self, ctx, *, query: str):
        """
        Play music from YouTube
        Usage: !play <song name or YouTube URL>
        """
        # Log command usage asynchronously
        asyncio.create_task(self._log_play_command(ctx, query))
        
        # Check if user is in a voice channel
        if not ctx.author.voice:
            await ctx.send("❌ You need to be in a voice channel to use this command!")
            return
        
        # Connect to voice channel if not already connected
        if not ctx.voice_client:
            channel = ctx.author.voice.channel
            await channel.connect()
            asyncio.create_task(self._log_voice_connect(ctx, channel.name))
        
        # Search for the song
        async with ctx.typing():
            result = await self.search_youtube(query)
            
            if not result:
                asyncio.create_task(self._log_no_results(ctx, query))
                await ctx.send("❌ No results found!")
                return
            
            # Add requester info
            result['requester'] = ctx.author
            
            # If something is playing, add to queue
            if ctx.voice_client.is_playing():
                queue = self.get_queue(ctx)
                queue.append(result)
                asyncio.create_task(self._log_add_to_queue(ctx, result, len(queue)))
                
                embed = discord.Embed(
                    title="📋 Added to Queue",
                    description=f"[{result['title']}]({result['url']})",
                    color=discord.Color.blue()
                )
                if result['thumbnail']:
                    embed.set_thumbnail(url=result['thumbnail'])
                embed.add_field(name="Duration", value=self.format_duration(result['duration']), inline=True)
                embed.add_field(name="Position", value=len(queue), inline=True)
                embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
                
                await ctx.send(embed=embed)
            else:
                # Play immediately to minimize URL expiration
                try:
                    player = await YTDLSource.from_url(result['url'], loop=self.bot.loop, stream=True)
                    ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                        self.play_next(ctx), self.bot.loop
                    ))
                    
                    # Log and send embed after playback starts
                    asyncio.create_task(self._log_and_announce_play(ctx, result, player))
                    
                except Exception as e:
                    asyncio.create_task(self._log_play_immediate_error(ctx, result, str(e)))
                    await ctx.send(f"❌ Error playing song: {str(e)}")

    async def _log_play_command(self, ctx, query):
        """Async logging for play command"""
        logger.info(f"Play command used by {ctx.author} in {ctx.guild}: '{query}'")

    async def _log_voice_connect(self, ctx, channel_name):
        """Async logging for voice connection"""
        logger.info(f"Connecting to voice channel: {channel_name}")
        log_music(ctx, "voice_connect", {"channel": channel_name})

    async def _log_no_results(self, ctx, query):
        """Async logging for no search results"""
        logger.warning(f"No results found for query: '{query}'")
        log_music(ctx, "search_no_results", {"query": query})

    async def _log_add_to_queue(self, ctx, result, queue_position):
        """Async logging for adding to queue"""
        logger.info(f"Added to queue: {result['title']} (position {queue_position})")
        log_music(ctx, "add_to_queue", result)

    async def _log_and_announce_play(self, ctx, result, player):
        """Async logging and announcement for immediate play"""
        logger.info(f"Playing immediately: {result['title']}")
        log_music(ctx, "play_now", result)
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[{player.title}]({result['url']})",
            color=discord.Color.green()
        )
        if player.thumbnail:
            embed.set_thumbnail(url=player.thumbnail)
        embed.add_field(name="Duration", value=self.format_duration(player.duration), inline=True)
        embed.add_field(name="Requested by", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

    async def _log_play_immediate_error(self, ctx, result, error):
        """Async logging for immediate play errors"""
        logger.error(f"Error playing song immediately: {error}")
        log_music(ctx, "play_error", result, error=error)

    @commands.command(name='pause', help='Pause the current song')
    async def pause(self, ctx):
        """Pause the current song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            asyncio.create_task(self._log_simple_command(ctx, "pause"))
            await ctx.send("⏸️ Music paused!")
        else:
            await ctx.send("❌ No music is playing!")

    @commands.command(name='resume', help='Resume the paused song')
    async def resume(self, ctx):
        """Resume the paused song"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            asyncio.create_task(self._log_simple_command(ctx, "resume"))
            await ctx.send("▶️ Music resumed!")
        else:
            await ctx.send("❌ Music is not paused!")

    @commands.command(name='skip', aliases=['s'], help='Skip the current song')
    async def skip(self, ctx):
        """Skip the current song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            asyncio.create_task(self._log_simple_command(ctx, "skip"))
            await ctx.send("⏭️ Song skipped!")
        else:
            await ctx.send("❌ No music is playing!")

    @commands.command(name='stop', help='Stop music and clear the queue')
    async def stop(self, ctx):
        """Stop music and clear the queue"""
        if ctx.voice_client:
            # Clear the queue
            queue_length = 0
            if ctx.guild.id in self.music_queues:
                queue_length = len(self.music_queues[ctx.guild.id])
                self.music_queues[ctx.guild.id] = []
            
            ctx.voice_client.stop()
            asyncio.create_task(self._log_stop_command(ctx, queue_length))
            await ctx.send("⏹️ Music stopped and queue cleared!")
        else:
            await ctx.send("❌ No music is playing!")

    async def _log_simple_command(self, ctx, action):
        """Async logging for simple commands"""
        logger.info(f"{action.title()} command used by {ctx.author} in {ctx.guild}")
        log_music(ctx, action)

    async def _log_stop_command(self, ctx, queue_length):
        """Async logging for stop command"""
        logger.info(f"Stop command used by {ctx.author} in {ctx.guild}")
        logger.info(f"Cleared queue of {queue_length} songs")
        log_music(ctx, "stop", {"queue_cleared": queue_length})

    @commands.command(name='queue', aliases=['q'], help='Show the music queue')
    async def queue(self, ctx):
        """Show the music queue"""
        queue = self.get_queue(ctx)
        
        if len(queue) == 0:
            await ctx.send("📋 The queue is empty!")
            return
        
        embed = discord.Embed(
            title="🎵 Music Queue",
            color=discord.Color.blue()
        )
        
        # Show up to 10 songs
        for i, song in enumerate(queue[:10], 1):
            embed.add_field(
                name=f"{i}. {song['title'][:50]}",
                value=f"Duration: {self.format_duration(song['duration'])} | Requested by: {song['requester'].mention}",
                inline=False
            )
        
        if len(queue) > 10:
            embed.set_footer(text=f"And {len(queue) - 10} more songs...")
        
        await ctx.send(embed=embed)

    @commands.command(name='nowplaying', aliases=['np'], help='Show the current song')
    async def nowplaying(self, ctx):
        """Show information about the current song"""
        if ctx.voice_client and ctx.voice_client.source:
            source = ctx.voice_client.source
            
            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"{source.title}",
                color=discord.Color.green()
            )
            if hasattr(source, 'thumbnail') and source.thumbnail:
                embed.set_thumbnail(url=source.thumbnail)
            if hasattr(source, 'duration'):
                embed.add_field(name="Duration", value=self.format_duration(source.duration), inline=True)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No music is playing!")

    @commands.command(name='volume', help='Change the volume (0-100)')
    async def volume(self, ctx, volume: int):
        """Change the player volume"""
        if not ctx.voice_client:
            await ctx.send("❌ Not connected to a voice channel!")
            return
        
        if volume < 0 or volume > 100:
            await ctx.send("❌ Volume must be between 0 and 100!")
            return
        
        ctx.voice_client.source.volume = volume / 100
        asyncio.create_task(self._log_volume_change(ctx, volume))
        await ctx.send(f"🔊 Volume set to {volume}%")

    async def _log_volume_change(self, ctx, volume):
        """Async logging for volume changes"""
        logger.info(f"Volume command used by {ctx.author} in {ctx.guild}: {volume}")
        log_music(ctx, "volume_change", {"volume": volume})

    @commands.command(name='leave', aliases=['disconnect', 'dc'], help='Disconnect the bot from voice')
    async def leave(self, ctx):
        """Disconnect from voice channel"""
        if ctx.voice_client:
            # Clear the queue
            queue_length = 0
            if ctx.guild.id in self.music_queues:
                queue_length = len(self.music_queues[ctx.guild.id])
                self.music_queues[ctx.guild.id] = []
            
            await ctx.voice_client.disconnect()
            asyncio.create_task(self._log_leave_command(ctx, queue_length))
            await ctx.send("👋 Disconnected from voice channel!")
        else:
            await ctx.send("❌ I'm not in a voice channel!")

    async def _log_leave_command(self, ctx, queue_length):
        """Async logging for leave command"""
        logger.info(f"Leave command used by {ctx.author} in {ctx.guild}")
        logger.info(f"Cleared queue of {queue_length} songs before leaving")
        log_music(ctx, "voice_disconnect")

    @commands.command(name='join', help='Join your voice channel')
    async def join(self, ctx):
        """Join the user's voice channel"""
        if not ctx.author.voice:
            await ctx.send("❌ You need to be in a voice channel!")
            return
        
        channel = ctx.author.voice.channel
        
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
            asyncio.create_task(self._log_voice_move(ctx, channel.name))
            await ctx.send(f"📍 Moved to {channel.name}")
        else:
            await channel.connect()
            asyncio.create_task(self._log_voice_join(ctx, channel.name))
            await ctx.send(f"🔊 Connected to {channel.name}")

    async def _log_voice_move(self, ctx, channel_name):
        """Async logging for voice channel move"""
        logger.info(f"Moved to voice channel: {channel_name}")
        log_music(ctx, "voice_move", {"channel": channel_name})

    async def _log_voice_join(self, ctx, channel_name):
        """Async logging for voice channel join"""
        logger.info(f"Connected to voice channel: {channel_name}")
        log_music(ctx, "voice_connect", {"channel": channel_name})

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Auto-leave when alone in voice channel"""
        if member.bot:
            return  # Ignore bot voice state changes
            
        voice_client = discord.utils.get(self.bot.voice_clients, guild=member.guild)
        
        if voice_client and voice_client.channel:
            # Log voice state changes asynchronously
            asyncio.create_task(self._log_voice_state_update(member, before, after))
            
            # Check if bot is alone in voice channel
            if len(voice_client.channel.members) == 1:
                asyncio.create_task(self._handle_alone_in_channel(voice_client, member.guild))

    async def _log_voice_state_update(self, member, before, after):
        """Async logging for voice state updates"""
        log_voice(member, before, after, "voice_state_update")

    async def _handle_alone_in_channel(self, voice_client, guild):
        """Handle being alone in voice channel"""
        channel_name = voice_client.channel.name
        logger.info(f"Bot is alone in {channel_name}, waiting 30 seconds...")
        await asyncio.sleep(30)  # Wait 30 seconds
        
        # Check again
        if voice_client.is_connected() and len(voice_client.channel.members) == 1:
            logger.info(f"Auto-leaving {channel_name} due to inactivity")
            # Clear queue
            if guild.id in self.music_queues:
                self.music_queues[guild.id] = []
            
            await voice_client.disconnect()

# Setup function
async def setup(bot):
    await bot.add_cog(Music(bot))
    logger.info("Music cog loaded successfully")