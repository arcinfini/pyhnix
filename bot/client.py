import asyncio
import logging
import os
import signal
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import asyncpg
import discord
from discord.ext import commands
from dotenv import load_dotenv

from bot import constants, errors
from bot.database import Database
from bot.team import TeamGuild
from bot.tree import PhoenixTree
from bot.utils.cache import Cache

_log = logging.getLogger(__name__)

load_dotenv()

if TYPE_CHECKING:
    from bot.utils.types import Context


class Phoenix(commands.Bot):
    """The client class used to control the bot."""

    def __init__(self) -> None:
        mentions = discord.AllowedMentions.none()
        mentions.users = True
        mentions.replied_user = True

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix=constants.Client.prefix,
            tree_cls=PhoenixTree,
            intents=intents,
            allowed_mentions=mentions,
        )

        self.add_listener(self.__awake_hook, "on_ready")
        self.__database: Optional[Database] = None
        self.__team_guild_cache: Cache[int, TeamGuild] = Cache()

    @property
    def database(self) -> Database:
        """The database to query."""
        if self.__database is None:
            raise Exception("The database connection is not established")

        return self.__database

    @property
    def tree(self) -> PhoenixTree:
        """The command tree linked with the custom client."""
        return super().tree  # type: ignore[return-value]

    async def __awake_hook(self) -> None:
        user = self.user
        if user is None:
            return

        _log.info("Awake as @%s#%s", user.name, user.discriminator)

    async def setup_hook(self) -> None:
        """Set up the client's extensions and graceful shutdown handler."""
        await self.__load_extensions(Path("bot/ext"))
        await self.ensure_database()

        async def shutdown() -> None:
            _log.info("client is closing")

            if self.__database:
                await self.__database.close()
            await self.close()

        def signal_handler() -> None:
            asyncio.create_task(shutdown())

        self.loop.add_signal_handler(signal.SIGINT, lambda: signal_handler())
        self.loop.add_signal_handler(signal.SIGTERM, lambda: signal_handler())

    async def __load_extensions(self, folder: Path) -> None:
        """Iterate over the extension folder to load all python files."""
        if not folder.is_dir():
            return

        for item in folder.iterdir():
            if item.name.startswith("_"):
                continue

            if item.is_dir():
                await self.__load_extensions(item)
                continue

            if item.suffix == ".py":
                await self.__try_load(item)

    async def __try_load(self, path: Path) -> bool:
        """Load a gear at the given path and returns the success state."""
        extension = ".".join(path.with_suffix("").parts)

        try:
            await self.load_extension(extension)
            return True
        except Exception:
            _log.exception("an error occurred while loading extension")
            return False

    async def ensure_database(self) -> Database:
        """Ensure the database is available through the pool connection.

        Uses env variables to connect to the postgres database through asyncpg.
        This bot requires on the use of postgres and will not function without
        it.
        """
        if self.__database is not None:
            return self.database

        _log.warn("Database connection: initializing")
        pool = await asyncpg.create_pool(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=5432,
            database=os.getenv("POSTGRES_DB"),
        )

        if pool is None:
            raise Exception("Pool is somehow None")

        self.__database = Database(pool)
        _log.warn("Database connection: initialized")

        return self.database

    def get_team_guild(self, guild: discord.Guild) -> TeamGuild:
        """Return a `TeamGuild` for the provided guild."""
        team_guild = self.__team_guild_cache.get(guild.id)
        if team_guild:
            return team_guild

        team_guild = TeamGuild(self.database, guild=guild)
        self.__team_guild_cache.put(guild.id, team_guild)

        return team_guild

    async def on_command_error(  # type: ignore[override]
        self, context: Context, error: commands.CommandError
    ) -> None:
        """Inform the user of the error if it is an internal error.

        Known internal errors are propogated to the user. Cases where code has
        failed, report the error to the user and alert devs.
        """
        if isinstance(error, commands.CommandInvokeError):
            embed = errors.InternalError().format_notif_embed(context)
            await context.send(embed=embed)

            await self.alert(context, error)

        elif isinstance(error, errors.InternalError):
            embed = error.format_notif_embed(context)
            await context.send(embed=embed)

            return None

        elif isinstance(error, commands.CheckFailure):
            user_shown_error = errors.CheckFailure(content=str(error))

            embed = user_shown_error.format_notif_embed(context)
            await context.send(embed=embed)

            return None

        embed = errors.InternalError(
            title=error.__class__.__name__, content=str(error)
        ).format_notif_embed(context)
        await context.send(embed=embed)

        return await super().on_command_error(context, error)

    async def alert(
        self, interaction: Context, error: commands.CommandError
    ) -> None:
        """TODO."""
