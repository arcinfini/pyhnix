from logging import getLogger
from pathlib import Path

from discord import AllowedMentions, Intents
from discord.ext import commands

from .tree import Tree

_log = getLogger(__name__)


class Client(commands.Bot):
    """An extension of the discord client for custom implementation."""

    def __init__(self) -> None:
        intents = Intents.all()
        mentions = AllowedMentions.all()
        mentions.everyone = False
        mentions.roles = False

        super().__init__(
            command_prefix="!",  # TODO HARDCODED
            intents=intents,
            allowed_mentions=mentions,
            tree_cls=Tree,
        )

    async def load_extension(
        self, loc: str, *, package: str | None = None
    ) -> None:
        """Load a module.

        An extension of the builtin load_extension function with exception
        handling.
        """
        try:
            await super().load_extension(loc)
        except Exception:
            _log.exception("Module failed to load")

    async def initialize_modules(self, loc: Path) -> None:
        """Load the client's modules.

        Parameters
        ----------
        `loc`: Path - the location to begin the iteration.

        A recursive method to walk over directory contents. The logic will pass
        over files and directories prefixed with an underscore. It will also
        pass over non python files.

        """
        if loc.name.startswith("_") or (
            loc.suffix != ".py" and not loc.is_dir()
        ):
            return

        _log.debug(f"{loc} {loc.is_dir()}")
        if not loc.is_dir() and loc.suffix == ".py":
            mod = ".".join(loc.with_suffix("").parts)
            await self.load_extension(mod)
            return

        for elem in loc.iterdir():
            await self.initialize_modules(elem)

    async def setup_hook(self) -> None:
        """Run essential setup for the client."""
        await self.initialize_modules(Path("bot/module"))

    async def on_error(self, event: str, /, *args, **kwargs) -> None:
        """Handle errors propogated from event handlers and other sources."""
        await super().on_error(event, *args, **kwargs)

    async def on_command_error(
        self, context: commands.Context, error: commands.CommandError
    ) -> None:
        """Handle errors propogated in relation to textual commands."""
        # TODO: implement handler here. these text commands are not meant to be
        # used by 'regular' users. therefore these errors should not be
        # propogated to the user. UNLESS a debug mode is enabled and then it
        # would make sense to avoid the jump to read logs.
        await super().on_command_error(context, error)
