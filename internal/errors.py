"""
Contains all internal errors for the program

Behavior for errors are within the InternalError class and alternations are made
in inherited classes. 
"""

from typing import Union

from discord.ext import commands
from discord import app_commands, Interaction, Embed

Info = Union[commands.Context, Interaction]


class InternalError(Exception):
    title = "Internal Error"
    content = "an unhandled internal error occurred. if this continues please inform an active bot dev"
    color = 0xC6612A

    def __init__(self, *, content: Union[str, None] = None):
        if content is not None:
            self.content = content

    def format_notif_embed(self, info: Info):
        # interaction = info if isinstance(info, Interaction) else None
        # context = info if isinstance(info, commands.Context) else None

        embed = Embed(
            title=self.title,
            color=self.color,
            description=self.content.format(info=info),
        )

        return embed


class CheckFailure(
    InternalError, app_commands.CheckFailure, commands.CheckFailure
):
    title = f"This command cannot be used"
    content = "Default: Bot Devs need to provide better info here"


class ClearanceError(CheckFailure):
    title = f"Invalid Authorization"
    content = "```\nYou do not have access to run this command\n```"


class InvalidInvocationError(CheckFailure):
    title = f"Invalid Invocation"
    content = "```\nThis command was ran in an invalid context\n```"


class InvalidParameterError(CheckFailure):
    title = f"Invalid Parameters"
    content = "The parameters you provided are not accepted in this context"


class TransformationError(InvalidParameterError):
    pass


class InitializationError(InternalError):
    pass