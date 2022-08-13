
from discord import app_commands, Interaction
from discord.ext import commands

class Main(commands.Cog, name="terminal"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sync_apps(self, ctx:commands.Context):
        self.bot.tree.copy_global_to(guild=ctx.guild)
        print(await self.bot.tree.sync(guild=ctx.guild))

    @app_commands.command(name="reload", description="reloads a bot extension")
    @app_commands.describe(extension="the extension to reload")
    async def _reload(self, interaction:Interaction, extension:str):
        """This is a bot dev command and access is restricted"""
        
        try:
            await self.bot.reload_extension(extension)
            await interaction.response.send_message("extension reload successful", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("reload failure %s" % str(e))

    @_reload.autocomplete('extension')
    async def _reload_choices(self, interaction: Interaction, current: str):
        contains = lambda x: current in x
        x = lambda x: app_commands.Choice(name=x, value=x)
        return [x(value) for value in filter(contains, self.bot.extensions)]


async def setup(bot):
    await bot.add_cog(Main(bot))