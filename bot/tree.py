import logging
from typing import Any, Optional, TYPE_CHECKING

import discord
from discord import app_commands
from discord.app_commands import AppCommandError, CommandTree
from discord.interactions import Interaction

from bot import errors

if TYPE_CHECKING:
    from discord.abc import Snowflake
    from discord.enums import AppCommandType

    from .client import Phoenix

_log = logging.getLogger(__name__)


class PhoenixTree(CommandTree):
    """The custom class for the command tree with the client."""

    async def interaction_check(self, interaction: Interaction) -> bool:
        """Return true after logging the interaction being used."""
        if (command := interaction.command) is not None:
            _log.debug(
                "interaction issued; by: %s, %d",
                command.qualified_name,
                interaction.user.id,
            )

        return True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.__commands_cache: dict = {}

    async def respond(
        self, interaction: Interaction["Phoenix"], *args: Any, **kwargs: Any
    ) -> None:
        """Either respond or send a followup on an interaction response."""
        if interaction.response.is_done():
            await interaction.followup.send(*args, **kwargs)

            return

        await interaction.response.send_message(*args, **kwargs)

    def clear_commands(
        self,
        *,
        guild: Optional["Snowflake"],
        type: Optional["AppCommandType"] = None,
    ) -> None:
        """Clear the commands from the local storage from the base tree.

        The commands are temporarily stored until restore_commands is called
        with the same guild.
        """
        commands = self.get_commands(guild=guild)
        self.__commands_cache[guild] = commands

        super().clear_commands(guild=guild)

    def restore_commands(self, /, guild: discord.Guild | None = None) -> None:
        """Read the commands from the internal cache and write to the tree.

        If no commands are temporarily stored, the code carries on.
        """
        try:
            commands = self.__commands_cache.pop(guild)
        except KeyError:
            pass
        else:
            for command in commands:
                self.add_command(command, guild=guild)

    async def on_error(
        self, interaction: Interaction["Phoenix"], error: AppCommandError
    ) -> None:
        """Inform the user of the error if it is an internal error.

        Known internal errors are propogated to the user. Cases where code has
        failed, report the error to the user and alert devs.
        """
        if isinstance(error, app_commands.CommandInvokeError):
            embed = errors.InternalError().format_notif_embed(interaction)
            await self.respond(interaction, embed=embed, ephemeral=True)

            await self.alert(interaction, error)

        if isinstance(error, errors.InternalError):
            embed = error.format_notif_embed(interaction)
            await self.respond(interaction, embed=embed, ephemeral=True)

            return

        if isinstance(error, app_commands.CheckFailure):
            user_shown_error = errors.CheckFailure(content=str(error))

            embed = user_shown_error.format_notif_embed(interaction)
            await self.respond(interaction, embed=embed, ephemeral=True)

            return

        embed = errors.InternalError(
            title=error.__class__.__name__, content=str(error)
        ).format_notif_embed(interaction)
        await self.respond(interaction, embed=embed, ephemeral=True)

        await super().on_error(interaction, error)

    async def alert(
        self, interaction: Interaction, error: AppCommandError
    ) -> None:
        """TODO."""
