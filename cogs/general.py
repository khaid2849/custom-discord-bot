import discord
from discord.ext import commands
from datetime import datetime
import random

class General(commands.Cog):
    """General commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready():
        """Called when the cog is ready"""
        print('General cog loaded')
    
    @commands.command(name='userinfo', help='Get information about a user')
    async def userinfo(self, ctx, member: discord.Member = None):
        """Shows information about a user"""
        # If no member specified, use the command author
        member = member or ctx.author
        
        # Create embed
        embed = discord.Embed(
            title=f"User Info - {member.name}",
            color=member.color if member.color != discord.Color.default() else discord.Color.blue()
        )
        
        # Set thumbnail to user avatar
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        # Add fields
        embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
        embed.add_field(name="Status", value=str(member.status).title(), inline=True)
        embed.add_field(name="Bot", value="Yes" if member.bot else "No", inline=True)
        embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        
        # Add roles
        roles = [role.mention for role in member.roles[1:]]  # Exclude @everyone
        if roles:
            embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles[:20]), inline=False)  # Limit to 20 roles
        
        # Set footer
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.timestamp = datetime.utcnow()
        
        await ctx.send(embed=embed)
    
    @commands.command(name='roll', help='Roll a dice')
    async def roll(self, ctx, dice: str = '1d6'):
        """
        Roll dice in NdN format
        Example: !roll 2d6 (rolls 2 six-sided dice)
        """
        try:
            rolls, limit = map(int, dice.split('d'))
        except ValueError:
            await ctx.send('❌ Format has to be NdN! (e.g., 1d6, 2d20)')
            return
        
        if rolls > 25:
            await ctx.send('❌ Too many dice! Maximum is 25.')
            return
        
        if limit > 100:
            await ctx.send('❌ Dice size too large! Maximum is 100.')
            return
        
        results = [random.randint(1, limit) for _ in range(rolls)]
        total = sum(results)
        
        embed = discord.Embed(
            title=f"🎲 Dice Roll: {dice}",
            color=discord.Color.green()
        )
        embed.add_field(name="Results", value=", ".join(map(str, results)), inline=False)
        embed.add_field(name="Total", value=str(total), inline=True)
        embed.add_field(name="Average", value=f"{total/rolls:.2f}", inline=True)
        embed.set_footer(text=f"Rolled by {ctx.author.name}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='choose', help='Choose between multiple options')
    async def choose(self, ctx, *choices: str):
        """
        Choose between multiple options
        Example: !choose pizza pasta salad
        """
        if not choices:
            await ctx.send('❌ You need to provide choices! Example: `!choose option1 option2`')
            return
        
        choice = random.choice(choices)
        await ctx.send(f'🤔 I choose: **{choice}**')
    
    @commands.command(name='clear', help='Clear messages from the channel')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 10):
        """
        Clear a specified number of messages
        Requires: Manage Messages permission
        """
        if amount < 1 or amount > 100:
            await ctx.send('❌ Please provide a number between 1 and 100')
            return
        
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
        
        # Send confirmation and delete it after 5 seconds
        msg = await ctx.send(f'✅ Deleted {len(deleted) - 1} messages')
        await msg.delete(delay=5)
    
    @commands.command(name='poll', help='Create a simple yes/no poll')
    async def poll(self, ctx, *, question: str):
        """
        Create a simple yes/no poll
        Example: !poll Should we have pizza for dinner?
        """
        embed = discord.Embed(
            title="📊 Poll",
            description=question,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Poll by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        # Send the poll
        poll_msg = await ctx.send(embed=embed)
        
        # Add reactions
        await poll_msg.add_reaction('✅')  # Yes
        await poll_msg.add_reaction('❌')  # No
        
        # Delete the command message
        await ctx.message.delete()
    
    @commands.command(name='avatar', help='Get user avatar')
    async def avatar(self, ctx, member: discord.Member = None):
        """Shows a user's avatar"""
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"{member.name}'s Avatar",
            color=member.color if member.color != discord.Color.default() else discord.Color.blue()
        )
        embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        
        await ctx.send(embed=embed)

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(General(bot))