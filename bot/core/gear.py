from logging import getLogger
from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from . import Client


_log = getLogger(__name__)


class Gear(commands.Cog):
    """An extension of the cog for custom implementations."""

    def __init__(self, client: "Client") -> None:
        self.client = client

    async def cog_load(self) -> None:
        """Log the initialization of the cog."""
        _log.info("Module loaded")

    async def cog_unload(self) -> None:
        """Log the deinitialization of the cog."""
        _log.info("Module unloaded")
