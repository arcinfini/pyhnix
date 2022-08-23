

from discord.ext import commands

from .utils import checks

async def is_bot_admin():
    """
    Checks if the author of the command is a bot admin
    """
    
    def predicate(ctx: commands.Context):
        return checks.is_bot_admin(ctx.author)
    return commands.check(predicate)