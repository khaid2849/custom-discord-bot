import discord
import asyncio
import yt_dlp as youtube_dl
import re

from discord.ext import commands


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

# YouTube DL options
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
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

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
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    """Music commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.music_queues = {}  # Guild ID -> List of songs
        
    def get_queue(self, ctx):
        """Get the music queue for a guild"""
        if ctx.guild.id not in self.music_queues:
            self.music_queues[ctx.guild.id] = []
        return self.music_queues[ctx.guild.id]
    
    async def play_next(self, ctx):
        """Play the next song in the queue"""
        queue = self.get_queue(ctx)
        if len(queue) > 0:
            # Get the next song
            next_song = queue.pop(0)
            
            # Create player and play
            try:
                player = await YTDLSource.from_url(next_song['url'], loop=self.bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next(ctx), self.bot.loop
                ))
                
                # Send now playing message
                embed = discord.Embed(
                    title="🎵 Now Playing",
                    description=f"[{player.title}]({next_song['url']})",
                    color=discord.Color.green()
                )
                if player.thumbnail:
                    embed.set_thumbnail(url=player.thumbnail)
                embed.add_field(name="Duration", value=self.format_duration(player.duration), inline=True)
                embed.add_field(name="Requested by", value=next_song['requester'].mention, inline=True)
                
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"❌ Error playing song: {str(e)}")
                await self.play_next(ctx)  # Try next song
    
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
        
        if url_pattern.match(query):
            # It's a URL, use it directly
            search_query = query
        else:
            # It's a search query
            search_query = f"ytsearch:{query}"
        
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))
            
            if 'entries' in data and data['entries']:
                # Get first result
                video = data['entries'][0]
                return {
                    'title': video.get('title', 'Unknown'),
                    'url': video.get('webpage_url', video.get('url')),
                    'duration': video.get('duration', 0),
                    'thumbnail': video.get('thumbnail'),
                    'channel': video.get('channel', 'Unknown')
                }
            elif 'title' in data:
                # Direct URL result
                return {
                    'title': data.get('title', 'Unknown'),
                    'url': data.get('webpage_url', data.get('url')),
                    'duration': data.get('duration', 0),
                    'thumbnail': data.get('thumbnail'),
                    'channel': data.get('channel', 'Unknown')
                }
        except Exception as e:
            print(f"Search error: {e}")
            return None
    
    @commands.command(name='play', aliases=['p'], help='Play music from YouTube')
    async def play(self, ctx, *, query: str):
        """
        Play music from YouTube
        Usage: !play <song name or YouTube URL>
        """
        # Check if user is in a voice channel
        if not ctx.author.voice:
            await ctx.send("❌ You need to be in a voice channel to use this command!")
            return
        
        # Connect to voice channel if not already connected
        if not ctx.voice_client:
            channel = ctx.author.voice.channel
            await channel.connect()
        
        # Search for the song
        async with ctx.typing():
            result = await self.search_youtube(query)
            
            if not result:
                await ctx.send("❌ No results found!")
                return
            
            # Add requester info
            result['requester'] = ctx.author
            
            # If something is playing, add to queue
            if ctx.voice_client.is_playing():
                queue = self.get_queue(ctx)
                queue.append(result)
                
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
                # Play immediately
                try:
                    player = await YTDLSource.from_url(result['url'], loop=self.bot.loop, stream=True)
                    ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                        self.play_next(ctx), self.bot.loop
                    ))
                    
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
                except Exception as e:
                    await ctx.send(f"❌ Error playing song: {str(e)}")
    
    @commands.command(name='pause', help='Pause the current song')
    async def pause(self, ctx):
        """Pause the current song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Music paused!")
        else:
            await ctx.send("❌ No music is playing!")
    
    @commands.command(name='resume', help='Resume the paused song')
    async def resume(self, ctx):
        """Resume the paused song"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Music resumed!")
        else:
            await ctx.send("❌ Music is not paused!")
    
    @commands.command(name='skip', aliases=['s'], help='Skip the current song')
    async def skip(self, ctx):
        """Skip the current song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Song skipped!")
        else:
            await ctx.send("❌ No music is playing!")
    
    @commands.command(name='stop', help='Stop music and clear the queue')
    async def stop(self, ctx):
        """Stop music and clear the queue"""
        if ctx.voice_client:
            # Clear the queue
            if ctx.guild.id in self.music_queues:
                self.music_queues[ctx.guild.id] = []
            
            ctx.voice_client.stop()
            await ctx.send("⏹️ Music stopped and queue cleared!")
        else:
            await ctx.send("❌ No music is playing!")
    
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
        await ctx.send(f"🔊 Volume set to {volume}%")
    
    @commands.command(name='leave', aliases=['disconnect', 'dc'], help='Disconnect the bot from voice')
    async def leave(self, ctx):
        """Disconnect from voice channel"""
        if ctx.voice_client:
            # Clear the queue
            if ctx.guild.id in self.music_queues:
                self.music_queues[ctx.guild.id] = []
            
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Disconnected from voice channel!")
        else:
            await ctx.send("❌ I'm not in a voice channel!")
    
    @commands.command(name='join', help='Join your voice channel')
    async def join(self, ctx):
        """Join the user's voice channel"""
        if not ctx.author.voice:
            await ctx.send("❌ You need to be in a voice channel!")
            return
        
        channel = ctx.author.voice.channel
        
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
            await ctx.send(f"📍 Moved to {channel.name}")
        else:
            await channel.connect()
            await ctx.send(f"🔊 Connected to {channel.name}")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Auto-leave when alone in voice channel"""
        voice_client = discord.utils.get(self.bot.voice_clients, guild=member.guild)
        
        if voice_client and voice_client.channel:
            # Check if bot is alone in voice channel
            if len(voice_client.channel.members) == 1:
                await asyncio.sleep(30)  # Wait 30 seconds
                
                # Check again
                if voice_client.is_connected() and len(voice_client.channel.members) == 1:
                    # Clear queue
                    if member.guild.id in self.music_queues:
                        self.music_queues[member.guild.id] = []
                    
                    await voice_client.disconnect()

# Setup function
async def setup(bot):
    await bot.add_cog(Music(bot))