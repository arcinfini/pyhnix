
from discord.ext import commands
import discord

class Main(commands.Cog, name=__name__):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Log event and apply basic role"""
        
        pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Log event"""
        
        pass

async def setup(bot):
    await bot.add_cog(Main(bot))