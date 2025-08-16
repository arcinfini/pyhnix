from discord import Embed, Interaction
from discord.ext import commands


class InternalError(Exception):
    """An internal error that servers as a wrapper around discord.py errors."""

    title: str = "Internal Error"
    content: str = (
        "an unhandle error occured. if this continues, submit a ticket."
    )
    color: int = 0xC6612A

    def __init__(self, *, error: Exception | None = None):
        self.cause = error

    def format_embed(self, info: commands.Context | Interaction) -> Embed:
        """Build an embed to be sent with error information."""
        return Embed(
            title=self.title,
            description=self.content.format(info=info),
            color=self.color,
        )

    async def alert(self, info: commands.Context | Interaction) -> None:
        """Alert the bot dev channel of an exception."""
        # TODO
