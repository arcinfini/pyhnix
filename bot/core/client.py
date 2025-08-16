from logging import getLogger
from pathlib import Path

from discord import AllowedMentions, Intents
from discord.ext import commands

from bot.util import Mode, SingletonBase

from . import error as errors
from .tree import Tree

_log = getLogger(__name__)


class Client(commands.Bot, SingletonBase):
    """An extension of the discord client for custom implementation."""

    def __init__(self) -> None:
        intents = Intents.all()
        mentions = AllowedMentions.all()
        mentions.everyone = False
        mentions.roles = False

        self.__mode: Mode | None = None

        super().__init__(
            command_prefix="!",  # TODO HARDCODED
            intents=intents,
            allowed_mentions=mentions,
            tree_cls=Tree,
        )

    @property
    def mode(self) -> Mode:
        """Return the mode the program is running in."""
        if self.__mode is None:
            raise Exception(
                "Client mode is not defined yet."
            )  # TODO better error
        return self.__mode

    @mode.setter
    def mode(self, v: Mode) -> None:
        """Set the mode the program is running in."""
        self.__mode = v

    async def load_extension(
        self, loc: str, *, package: str | None = None
    ) -> None:
        """Load a module.

        Parameters
        ----------
        loc : `Path`
            the module path to load.
        package: Optional[`str`]
            The package name to resolve relative imports with.

        An extension of the builtin load_extension function with exception
        handling.

        """
        try:
            await super().load_extension(loc, package=package)
        except commands.NoEntryPointError:
            _log.error("Module has no entrypoint: %s", loc)
        except Exception:
            _log.exception("Module failed to load: %s", loc)

    async def initialize_modules(self, loc: Path) -> None:
        """Load the client's modules.

        Parameters
        ----------
        loc : `Path`
            the location to begin the iteration.

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

    async def on_error(self, event: str, /, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        """Handle errors propogated from event handlers and other sources."""
        await super().on_error(event, *args, **kwargs)

    async def on_command_error(
        self, context: commands.Context, error: commands.CommandError
    ) -> None:
        """Handle errors propogated in relation to textual commands."""
        if isinstance(error, commands.CommandNotFound):
            return

        _log.exception(
            "an unhandled exception occured in command or event", error
        )
        if self.mode != Mode.DEV:
            return

        unhandled = errors.InternalError(error=error)
        await context.send(embed=unhandled.format_embed(context))
        await unhandled.alert(context)
