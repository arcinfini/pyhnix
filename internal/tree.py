import traceback, io, logging
from discord import app_commands, Interaction
import discord

from internal import app_errors

logger = logging.getLogger(__name__)

class PhoenixTree(app_commands.CommandTree):
    """"""

    async def maybe_responded(self, interaction: Interaction, *args, **kwargs):

        if interaction.response.is_done():
            await interaction.followup.send(*args, **kwargs)
        
        else:
            await interaction.response.send_message(*args, **kwargs)

    async def interaction_check(self, interaction: Interaction):
        if (command := interaction.command) is not None:

            logger.debug("interaction issued; by: %s, %d", command.qualified_name, interaction.user.id)

        return True

    async def alert(self, interaction: Interaction, error: Exception):
        """
        Attempts to altert the discord channel logs of an exception
        """

        channel = await interaction.client.fetch_channel(1009624603942981742)

        content = traceback.format_exc()

        file = discord.File(
            io.BytesIO(bytes(content, encoding="UTF-8")), 
            filename=f"{type(error)}.py"
        )

        embed = discord.Embed(
            title="Unhandled Exception Alert",
            description=f"```\nContext: \nguild:{repr(interaction.guild)}\n{repr(interaction.channel)}\n{repr(interaction.user)}\n```" #f"```py\n{content[2000:].strip()}\n```"
        )

        await channel.send(embed=embed, file=file)

    async def on_error(self, interaction: Interaction, error: Exception):
        # check error
            # ClearanceError (the user does not have the valid role clearance)
        # input error
            # transformer conversion error (the transformer did not produce a valid variable)

        # environment error (this command was done in the wrong location)

        # if not caught, send error to discord logs

        if isinstance(error, app_errors.ClearanceError):

            embed = discord.Embed(
                "Clearance Error", 
                description=str(error),
                color=discord.Color.yellow()
            )

            await self.maybe_responded(interaction, embed=embed, ephemeral=True)
            return
        elif isinstance(error, app_errors.TransformationError):
            embed = discord.Embed(
                "Transformation Error", 
                description=str(error),
                color=discord.Color.yellow()
            )

            await self.maybe_responded(interaction, embed=embed, ephemeral=True)
            return

        await self.maybe_responded(
            interaction, 
            "an unhandled error occured, notifying the bot dev",
            ephemeral=True
        )

        try: await self.alert(interaction, error)
        except Exception as e: await super().on_error(interaction, e)

        await super().on_error(interaction, error)