from typing import TYPE_CHECKING

from discord import Embed
from discord.app_commands.errors import CheckFailure as AppCheckFailure
from discord.ext.commands import CheckFailure as CommandCheckFailure
from discord.ext.commands import Context
from discord.interactions import Interaction

if TYPE_CHECKING:
    from bot.client import Phoenix


class InternalError(Exception):
    """The base class used for internally caused errors."""

    title = "Internal Error"
    content = (
        "an unhandled internal error occurred. if this continues "
        "please submit a ticket"
    )
    color = 0xC6612A

    def __init__(self, *, title: str | None = None, content: str | None = None):
        if content is not None:
            self.content = content

        if title is not None:
            self.title = title

    def format_notif_embed(
        self, info: Context["Phoenix"] | Interaction["Phoenix"]
    ) -> Embed:
        """Build an embed with exception info to display in discord."""
        return Embed(
            title=self.title,
            color=self.color,
            description=self.content.format(info=info),
        )


class CheckFailure(InternalError, AppCheckFailure, CommandCheckFailure):
    """The base class used for internal check errors."""

    title = "You can not use this command"
    content = "Default, Bot Devs need to provide better info here"


class InvalidAuthorizationError(CheckFailure):
    """Represents a check failure caused by someone with invalid auth."""

    title = "Invalid Authorization"
    content = "```\nYou do not have access to run this command\n```"


class InvalidInvocationError(CheckFailure):
    """Represents an error state with an invalid state."""

    title = "Invalid Invocation"
    content = "```\nThis command can not be ran here\n```"


class InvalidParameterError(CheckFailure):
    """Represents an error state with invalid parameter provided."""

    title = "Invalid Parameters"
    content = "The information provided to the command was invalid"


class TransformationError(InvalidParameterError):
    """Represents an error state when a transformation fails."""


class InitializationError(InternalError):
    """Represents an error state when the bot should be logged in but is not."""
