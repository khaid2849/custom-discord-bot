import discord
import os
import asyncio
import subprocess
import sys

from discord.ext import commands
from dotenv import load_dotenv
from config import Config
from logger import get_logger, log_command, log_bot

load_dotenv()

logger = get_logger("Main")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True

bot = commands.Bot(
    command_prefix=Config.COMMAND_PREFIX,
    intents=intents,
    help_command=commands.DefaultHelpCommand()
)

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord"""
    logger.info(f'{bot.user.name} has connected to Discord!')
    logger.info(f'Bot ID: {bot.user.id}')
    logger.info(f'Guild Count: {len(bot.guilds)}')
    
    for guild in bot.guilds:
        logger.info(f'Connected to guild: {guild.name} (ID: {guild.id}) with {guild.member_count} members')
    
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot ID: {bot.user.id}')
    print(f'Guild Count: {len(bot.guilds)}')
    print('------')
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=Config.BOT_STATUS
        )
    )
    
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash command(s)")
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
        print(f"Failed to sync commands: {e}")
    
    log_bot("bot_ready", {
        "bot_name": bot.user.name,
        "bot_id": bot.user.id,
        "guild_count": len(bot.guilds),
        "synced_commands": len(synced) if 'synced' in locals() else 0
    })

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for commands"""
    logger.error(f"Command error in {ctx.command}: {error}")
    log_command(ctx, ctx.command.name if ctx.command else "unknown", success=False, error=error)
    
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ I don't have the required permissions to do that.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏱️ Command on cooldown. Try again in {error.retry_after:.2f} seconds.")
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")
        logger.error(f"Unhandled error: {error}", exc_info=True)

@bot.event
async def on_command_completion(ctx):
    """Log successful command completion"""
    log_command(ctx, ctx.command.name, success=True)

@bot.event
async def on_guild_join(guild):
    """Log when bot joins a guild"""
    logger.info(f"Joined guild: {guild.name} (ID: {guild.id}) with {guild.member_count} members")
    log_bot("guild_join", {
        "guild_name": guild.name,
        "guild_id": guild.id,
        "member_count": guild.member_count
    })

@bot.event
async def on_guild_remove(guild):
    """Log when bot leaves a guild"""
    logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
    log_bot("guild_leave", {
        "guild_name": guild.name,
        "guild_id": guild.id
    })

@bot.command(name='announce', help='Make the bot announce a message')
async def announce(ctx, *, message: str):
    """
    Makes the bot announce a message
    Usage: !announce <message>
    """
    logger.info(f"Announcement command used by {ctx.author} in {ctx.guild}")
    
    await ctx.message.delete()
    
    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=discord.Color.blue(),
        timestamp=ctx.message.created_at
    )
    embed.set_footer(text=f"Announced by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    
    await ctx.send(embed=embed)

@bot.command(name='ping', help='Check bot latency')
async def ping(ctx):
    """Shows the bot's latency"""
    latency = round(bot.latency * 1000)
    logger.debug(f"Ping command: {latency}ms latency")
    await ctx.send(f'🏓 Pong! Latency: {latency}ms')

@bot.command(name='echo', help='Repeat a message')
async def echo(ctx, *, message: str):
    """Repeats the user's message"""
    logger.debug(f"Echo command used by {ctx.author}: {message}")
    await ctx.send(f"{ctx.author.mention} said: {message}")

@bot.command(name='serverinfo', help='Get server information')
async def serverinfo(ctx):
    """Shows information about the current server"""
    guild = ctx.guild
    logger.debug(f"Server info requested for {guild.name}")
    
    embed = discord.Embed(
        title=f"Server Info - {guild.name}",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
    embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
    
    await ctx.send(embed=embed)

@bot.tree.command(name='hello', description='Say hello to the bot')
async def hello(interaction: discord.Interaction):
    """Simple slash command example"""
    logger.debug(f"Hello slash command used by {interaction.user}")
    await interaction.response.send_message(f'Hello {interaction.user.mention}! 👋')

@bot.tree.command(name='say', description='Make the bot say something')
async def say(interaction: discord.Interaction, message: str):
    """Slash command with parameters"""
    logger.debug(f"Say slash command used by {interaction.user}: {message}")
    await interaction.response.send_message(f"{message}")

@bot.tree.command(name='announce_slash', description='Announce a message using slash command')
async def announce_slash(interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
    """Advanced slash command for announcements"""
    logger.info(f"Slash announcement by {interaction.user} in {interaction.guild}")
    
    target_channel = channel or interaction.channel
    
    if not target_channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message("❌ I don't have permission to send messages in that channel!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=discord.Color.gold(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Announced by {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    
    await target_channel.send(embed=embed)
    
    await interaction.response.send_message(f"✅ Announcement sent to {target_channel.mention}!", ephemeral=True)

async def load_extensions():
    """Load all cogs from the cogs directory"""
    if not os.path.exists('./cogs'):
        os.makedirs('./cogs')
        logger.info('Created cogs directory')
        print('Created cogs directory')
    
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('_'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f'Loaded cog: {filename[:-3]}')
                print(f'Loaded cog: {filename[:-3]}')
            except Exception as e:
                logger.error(f'Failed to load cog {filename[:-3]}: {e}')
                print(f'Failed to load cog {filename[:-3]}: {e}')

@bot.command(name='logs', help='Get recent log information (Admin only)')
@commands.has_permissions(administrator=True)
async def logs(ctx, lines: int = 10):
    """Show recent log entries"""
    try:
        with open('logs/bot.log', 'r') as f:
            log_lines = f.readlines()
            recent_logs = log_lines[-lines:] if len(log_lines) >= lines else log_lines
            
        embed = discord.Embed(
            title=f"📋 Recent {len(recent_logs)} Log Entries",
            description=f"```\n{''.join(recent_logs)[:1900]}\n```",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        
    except FileNotFoundError:
        await ctx.send("❌ Log file not found!")
    except Exception as e:
        await ctx.send(f"❌ Error reading logs: {e}")

def upgrade_yt_dlp():
    """Upgrade yt-dlp to the latest version"""
    try:
        logger.info("Upgrading yt-dlp...")
        print("🔄 Upgrading yt-dlp to latest version...")
        
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "yt-dlp", "--upgrade"
        ], capture_output=True, text=True, check=True)
        
        logger.info("yt-dlp upgrade completed successfully")
        print("✅ yt-dlp upgraded successfully")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to upgrade yt-dlp: {e}")
        logger.error(f"Error output: {e.stderr}")
        print(f"❌ Failed to upgrade yt-dlp: {e}")
        print("Bot will continue running with current yt-dlp version...")
    except Exception as e:
        logger.error(f"Unexpected error during yt-dlp upgrade: {e}")
        print(f"❌ Unexpected error during yt-dlp upgrade: {e}")
        print("Bot will continue running...")

async def main():
    """Main function to run the bot"""
    # Upgrade yt-dlp before starting the bot
    upgrade_yt_dlp()
    
    logger.info("Starting Discord bot...")
    log_bot("bot_starting")
    
    async with bot:
        await load_extensions()
        try:
            await bot.start(Config.DISCORD_TOKEN)
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            log_bot("bot_start_failed", {"error": str(e)})
            raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
        log_bot("bot_shutdown", {"reason": "user_interrupt"})
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        log_bot("bot_crashed", {"error": str(e)})
        raise