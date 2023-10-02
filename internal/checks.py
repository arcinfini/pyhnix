from typing import Union

from .utils import helper

from discord.ext import commands
from discord import Interaction, app_commands


def check(predicate):
    """
    This is a custom check decorator that works for both app_commands and
    regular text commands
    """

    def true_decorator(decked_func):
        if isinstance(decked_func, app_commands.Command):
            app_commands.check(predicate)(decked_func)

        elif isinstance(decked_func, commands.Command):
            commands.check(predicate)(decked_func)

        else:
            app_commands.check(predicate)(decked_func)
            commands.check(predicate)(decked_func)

        return decked_func

    return true_decorator


def is_bot_admin():
    """
    Checks if the author of the command is a bot admin
    """

    def predicate(info: Interaction | commands.Context):
        user = info.user if isinstance(info, Interaction) else info.author

        return helper.is_bot_admin(user)

    return check(predicate)
