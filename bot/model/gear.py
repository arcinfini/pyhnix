import logging

from discord.ext import commands

from bot.client import Phoenix


class Gear(commands.Cog):
    """An extension of commands.Cog used by internal cogs."""

    def __init__(self, client: Phoenix) -> None:
        super().__init__()

        self.client = client

        self._log = logging.getLogger(self.__class__.__module__)

    async def cog_load(self) -> None:
        """Begin loading the cog."""
        await self.on_load()

        self._log.info("LOADED")

    async def on_load(self) -> None:
        """Load necessary content for the gear to run.

        Used by gears for cog loading, cog_load is used internally by the gear.
        """
