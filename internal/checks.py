

from discord.ext import commands
from .utils import helper

def is_bot_admin():
    """
    Checks if the author of the command is a bot admin
    """
    
    def predicate(ctx: commands.Context):
        return helper.is_bot_admin(ctx.author)
    return commands.check(predicate)