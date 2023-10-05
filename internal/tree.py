import traceback, io, logging, typing
from discord import app_commands, Interaction
import discord

from internal import errors


if typing.TYPE_CHECKING:
    from .client import Phoenix

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
            logger.debug(
                "interaction issued; by: %s, %d",
                command.qualified_name,
                interaction.user.id,
            )

        return True

    async def alert(
        self, interaction: Interaction["Phoenix"], error: Exception
    ):
        """
        Attempts to altert the discord channel logs of an exception
        """
        log_channe_id = interaction.client.config["ids"]["locations"][
            "error-logs"
        ]["channel"]

        channel = await interaction.client.fetch_channel(log_channe_id)

        content = traceback.format_exc()

        file = discord.File(
            io.BytesIO(bytes(content, encoding="UTF-8")),
            filename=f"{type(error)}.py",
        )

        embed = discord.Embed(
            title="Unhandled Exception Alert",
            description=f"""```
                Context:
                guild:{repr(interaction.channel)}
                {repr(interaction.user)}
            ```""",
        )

        if not isinstance(channel, discord.TextChannel):
            return

        await channel.send(embed=embed, file=file)

    async def on_error(
        self,
        interaction: Interaction["Phoenix"],
        error: app_commands.AppCommandError,
    ):
        logger.debug("error reached: %s", type(error))

        """Handles errors thrown within the command tree"""
        if isinstance(error, errors.InternalError):
            # Inform user of failure ephemerally

            embed = error.format_notif_embed(interaction)
            await self.maybe_responded(interaction, embed=embed, ephemeral=True)

            return
        elif isinstance(error, app_commands.CheckFailure):
            user_shown_error = errors.CheckFailure(content=str(error))

            embed = user_shown_error.format_notif_embed(interaction)
            await self.maybe_responded(interaction, embed=embed, ephemeral=True)

            return

        # most cases this will consist of errors thrown by the actual code

        user_shown_error = errors.InternalError()
        await self.maybe_responded(
            interaction,
            embed=user_shown_error.format_notif_embed(interaction),
            ephemeral=True,
        )

        try:
            await self.alert(interaction, error)
        except Exception as e:
            exception = app_commands.AppCommandError(str(e))

            await super().on_error(interaction, exception)

        await super().on_error(interaction, error)
