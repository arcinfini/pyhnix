from os import getenv
from pathlib import Path

from discord.ext import commands
import discord

from dotenv import load_dotenv

load_dotenv()

class Phoenix(commands.Bot):
    """"""

    def __init__(self, *args, namespace, **kwargs):
        super().__init__(command_prefix="!", *args, **kwargs)

        self.guild = discord.Object(id=namespace.guild)

    async def load_extensions(self, dir):
        """Recursively load extensions from the given directory"""
        
        if dir is None: return
        extdir = Path(dir)

        if not extdir.is_dir(): return

        for item in extdir.iterdir():
            if item.name.startswith("_"): continue
            if item.is_dir():
                await self.load_extensions(item)
                continue

            if item.suffix == ".py":
                extension = ".".join(item.with_suffix('').parts)

                try:
                    await self.load_extension(extension)
                except Exception as e:
                    print(str(e)) # turn into log

    async def run(self, token:str):

        await self.start(getenv(token))

    