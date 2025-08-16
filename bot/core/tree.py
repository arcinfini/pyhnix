from logging import getLogger
from typing import TYPE_CHECKING

from discord import Interaction
from discord.app_commands import AppCommandError, CommandTree

from bot.util import Mode

from . import errors

_log = getLogger(__name__)

if TYPE_CHECKING:
    from . import Client


class Tree(CommandTree):
    """An extension of the command tree for custom implementation."""

    client: "Client"

    async def maybe_responded(
        self,
        interaction: Interaction,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> None:
        """Send a response or edit an existing response.

        Only a single response can be sent after the interaction from a user.
        Therefore in the case where it is unclear if a response has been sent
        yet, this function should be used.

        Parameters
        ----------
        interaction: `Interaction`
            The interaction object to respond to.
        *args
            This function passes all args provided to the response method.
        **kwargs
            This function passes all kwargs provided to the response method.

        """
        if interaction.response.is_done():
            await interaction.response.edit_message(*args, **kwargs)
            return

        await interaction.response.send_message(*args, **kwargs)

    async def on_error(
        self, interaction: Interaction, error: AppCommandError
    ) -> None:
        """Handle errors propogated in relation to application commands."""
        _log.exception(
            "an unhandled exception occured in command or event", error
        )
        if self.client.mode != Mode.DEV:
            return

        unhandled = errors.InternalError(error=error)
        await self.maybe_responded(
            interaction,
            ephemeral=True,
            embed=unhandled.format_embed(interaction),
        )
        await unhandled.alert(interaction)
