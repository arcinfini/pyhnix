import logging
from os import getenv
from pathlib import Path

from discord.ext import commands
import discord, motor.motor_asyncio

from dotenv import load_dotenv

from internal.tree import PhoenixTree

load_dotenv()

logger = logging.getLogger(__name__)

class Phoenix(commands.Bot):
    """"""

    def __init__(self, *args, namespace, **kwargs):
        super().__init__(command_prefix="!", *args, tree_cls=PhoenixTree, **kwargs)

        self.guild = discord.Object(id=namespace.guild)
        self.add_listener(self.__awake_hook, "on_ready")

    async def __awake_hook(self):
        logger.info("Awake")

    async def setup_hook(self):
        await self.__load_extensions("ext")

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
                    print(str(e)) # turn into log

    def run(self, token:str):
        self.__motor = motor.motor_asyncio.AsyncIOMotorClient(token)

        super().run(getenv(token), log_handler=None)

    @property
    def database(self):
        return self.__motor['elonesports']