import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from config import Config

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
intents.guilds = True
intents.guild_messages = True

# Create bot instance
bot = commands.Bot(
    command_prefix=Config.COMMAND_PREFIX,
    intents=intents,
    help_command=commands.DefaultHelpCommand()
)

# Event: Bot is ready
@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord"""
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot ID: {bot.user.id}')
    print(f'Guild Count: {len(bot.guilds)}')
    print('------')
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=Config.BOT_STATUS
        )
    )
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Event: Error handler
@bot.event
async def on_command_error(ctx, error):
    """Global error handler for commands"""
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
        print(f"Unhandled error: {error}")

# Basic Commands
@bot.command(name='announce', help='Make the bot announce a message')
async def announce(ctx, *, message: str):
    """
    Makes the bot announce a message
    Usage: !announce <message>
    """
    # Delete the command message (optional)
    await ctx.message.delete()
    
    # Create an embed for better formatting
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
    await ctx.send(f'🏓 Pong! Latency: {latency}ms')

@bot.command(name='echo', help='Repeat a message')
async def echo(ctx, *, message: str):
    """Repeats the user's message"""
    await ctx.send(f"{ctx.author.mention} said: {message}")

@bot.command(name='serverinfo', help='Get server information')
async def serverinfo(ctx):
    """Shows information about the current server"""
    guild = ctx.guild
    
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

# Slash Commands
@bot.tree.command(name='hello', description='Say hello to the bot')
async def hello(interaction: discord.Interaction):
    """Simple slash command example"""
    await interaction.response.send_message(f'Hello {interaction.user.mention}! 👋')

@bot.tree.command(name='say', description='Make the bot say something')
async def say(interaction: discord.Interaction, message: str):
    """Slash command with parameters"""
    await interaction.response.send_message(f"{message}")

@bot.tree.command(name='announce_slash', description='Announce a message using slash command')
async def announce_slash(interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
    """Advanced slash command for announcements"""
    # Use the current channel if no channel is specified
    target_channel = channel or interaction.channel
    
    # Check if bot has permissions to send messages in the target channel
    if not target_channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message("❌ I don't have permission to send messages in that channel!", ephemeral=True)
        return
    
    # Create announcement embed
    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=discord.Color.gold(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Announced by {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    
    # Send to target channel
    await target_channel.send(embed=embed)
    
    # Confirm to the user
    await interaction.response.send_message(f"✅ Announcement sent to {target_channel.mention}!", ephemeral=True)

# Load cogs (command groups)
async def load_extensions():
    """Load all cogs from the cogs directory"""
    # Create cogs directory if it doesn't exist
    if not os.path.exists('./cogs'):
        os.makedirs('./cogs')
        print('Created cogs directory')
    
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('_'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded cog: {filename[:-3]}')
            except Exception as e:
                print(f'Failed to load cog {filename[:-3]}: {e}')

# Main function
async def main():
    """Main function to run the bot"""
    async with bot:
        await load_extensions()
        await bot.start(Config.DISCORD_TOKEN)

# Run the bot
if __name__ == '__main__':
    asyncio.run(main())