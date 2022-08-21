import logging

from discord import app_commands, Interaction
from discord.ext import commands

logger = logging.getLogger(__name__)

class Main(commands.Cog, name="terminal"):

    def __init__(self, bot):
        self.bot = bot

        logger.info("%s initialized" % __name__)

    @commands.command()
    async def sync_apps(self, ctx:commands.Context):
        self.bot.tree.copy_global_to(guild=ctx.guild)
        synced = await self.bot.tree.sync(guild=ctx.guild)
        logger.info(synced)

    @app_commands.command(name="reload", description="reloads a bot extension")
    @app_commands.describe(extension="the extension to reload")
    async def _reload(self, interaction:Interaction, extension:str):
        """This is a bot dev command and access is restricted"""
        
        try:
            await self.bot.reload_extension(extension)
            await interaction.response.send_message(
                "extension reload successful", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message("reload failure %s" % str(e))
            logger.error("reload failure in %s", extension, exc_info=e)
            raise e # send to tree error handler

    @_reload.autocomplete('extension')
    async def _reload_choices(self, interaction: Interaction, current: str):
        contains = lambda x: current in x
        x = lambda x: app_commands.Choice(name=x, value=x)
        return [x(value) for value in filter(contains, self.bot.extensions)]

    @app_commands.command(name="kill")
    async def _kill(self, interaction: Interaction):
        
        await interaction.response.send_message("TERMINATING")
        logger.critical("Terminating connection via command 'kill'")
        
        
        await interaction.client.close()


async def setup(bot):
    await bot.add_cog(Main(bot))