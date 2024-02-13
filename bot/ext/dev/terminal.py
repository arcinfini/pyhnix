import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from bot import errors
from bot.client import Phoenix
from bot.utils import checks

if TYPE_CHECKING:
    from bot.utils.types import Context, Interaction


logger = logging.getLogger(__name__)


class SyncFlags(commands.FlagConverter, delimiter=" ", prefix="--"):
    """A `FlagConverter` to build extra options for the sync command."""

    guild: discord.Guild | None = commands.flag(
        default=None, description="the guild to sync to"
    )
    clear: bool = commands.flag(default=False, description="clears commands")
    debug: bool = commands.flag(
        default=False,
        description="specifies if global commands should be copied to guild",
        name="copy_global",
    )


class Main(commands.Cog, name="terminal"):
    """A module for dev commands."""

    def __init__(self, client: Phoenix) -> None:
        self.client = client

        logger.info("%s initialized" % __name__)

    @commands.command(name="sync")
    @checks.bot_dev()
    async def _sync(self, ctx: "Context", *, flags: SyncFlags) -> None:
        """Sync application commands based on arguments provided.

        Default behavior syncs all commands as provided by the code.

        The flags for this command allow for local testing, clearing of all
        applications and specific guild syncing only.

        Because of behavior, global commands and local guild specific commands
        must be synced separately.
        """
        if flags.debug is True:
            if flags.guild is None:
                raise errors.InvalidParameterError(
                    content="guild must be specified if debug is true"
                )

            self.client.tree.copy_global_to(guild=flags.guild)

        if flags.clear is True:
            self.client.tree.clear_commands(guild=flags.guild)

        num_commands = len(self.client.tree.get_commands(guild=flags.guild))
        message = await ctx.send("Syncing %i commands" % num_commands)

        await self.client.tree.sync(guild=flags.guild)

        self.client.tree.restore_commands(guild=flags.guild)

        await message.edit(
            content="Synced %i commands" % num_commands, delete_after=5
        )

    @app_commands.command(name="reload", description="reloads a bot extension")
    @app_commands.describe(extension="the extension to reload")
    @app_commands.guilds(970761243277266944)
    @checks.bot_dev()
    async def _reload(self, interaction: "Interaction", extension: str) -> None:
        """Reload or load an extension."""
        try:
            await self.client.reload_extension(extension)
            await interaction.response.send_message(
                "extension reload successful", ephemeral=True
            )
        except commands.ExtensionError as e:
            await interaction.response.send_message(
                "reload failure %s" % str(e)
            )
            logger.error("reload failure in %s", extension, exc_info=e)
            raise e

    @_reload.autocomplete("extension")
    async def _reload_choices(
        self, interaction: "Interaction", current: str
    ) -> list[Choice[str]]:
        """Provide choices for autocompleting extensions."""
        contains = lambda x: current in x
        x = lambda x: Choice(name=x, value=x)
        return [x(value) for value in filter(contains, self.client.extensions)]

    @app_commands.command(name="kill")
    @app_commands.guilds(970761243277266944)
    @checks.bot_dev()
    async def _kill(self, interaction: "Interaction") -> None:
        """Close the connection to discord and exit the code."""
        await interaction.response.send_message("TERMINATING")
        logger.critical("Terminating connection via command 'kill'")

        await interaction.client.close()


async def setup(bot: Phoenix) -> None:
    """Load the terminal module."""
    await bot.add_cog(Main(bot))
