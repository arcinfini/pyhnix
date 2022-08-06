
from discord.ext import commands

class Main(commands.Cog, name="terminal"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sync_apps(self, ctx:commands.Context):
        
        await self.bot.tree.sync(guild=ctx.guild)

async def setup(bot):
    await bot.add_cog(Main(bot))