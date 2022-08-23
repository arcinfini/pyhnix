import logging, signal, asyncio, os
from pathlib import Path

from dotenv import load_dotenv
from discord.ext import commands
import discord, asyncpg

from internal.tree import PhoenixTree

logger = logging.getLogger(__name__)

load_dotenv()

class Phoenix(commands.Bot):
    """"""

    def __init__(self, namespace):
        mentions = discord.AllowedMentions.none()
        mentions.users = True
        mentions.replied_user = True

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        
        super().__init__(
            command_prefix=namespace.prefix, 
            tree_cls=PhoenixTree,
            intents=intents,
            allowed_mentions=mentions
        )

        self.namespace = namespace
        self.guild = discord.Object(id=namespace.guild)
        self.add_listener(self.__awake_hook, "on_ready")
        self.__pool = None

    async def __awake_hook(self):
        logger.info("Awake as @%s#%s", self.user.name, self.user.discriminator)

    async def setup_hook(self):
        """
        Sets up important extensions for the bot
        """
        
        await self.ensure_database()
        
        await self.__load_extensions("ext")

        # Not sure if this actually works.
        def handle_close(*args, **kwargs):
            logger.info("Recieved SIGTERM, terminating")
            asyncio.run(self.close())

        signal.signal(signal.SIGTERM, handle_close)

    async def __load_extensions(self, dir):
        """Recursively load extensions from the given directory"""
        
        if dir is None: return
        extdir = Path(dir)

        if not extdir.is_dir(): return

        for item in extdir.iterdir():
            if item.name.startswith("_"): continue
            if item.is_dir():
                await self.__load_extensions(item)
                continue

            if item.suffix == ".py":
                extension = ".".join(item.with_suffix('').parts)

                try:
                    await self.load_extension(extension)
                except Exception as e:
                    logger.error(
                        "an error occurred while loading extension", 
                        exc_info=e
                    )

    async def ensure_database(self):
        """
        Ensures the database is available through the pool connection

        Uses env variables to connect to the postgres database through asyncpg.
        This bot requires on the use of postgres and will not function without
        it.
        """

        if self.__pool is not None and not self.__pool._closed: return

        logger.warn("Database connection: initializing")
        self.__pool = await asyncpg.create_pool(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=self.namespace.host,
            port=5432,
            database=os.getenv('POSTGRES_DB')
        )
        logger.warn("Database connection: initialized")

    def run(self, token:str):
        
        super().run(token, log_handler=None)

    @property
    def database(self):
        return self.__pool