from collections.abc import Callable, Coroutine
from typing import Any, TYPE_CHECKING, Union

from discord.app_commands import (
    Command as SlashCommand,
)
from discord.app_commands import (
    ContextMenu,
)
from discord.app_commands import (
    check as slash_check,
)
from discord.ext.commands import (
    Command as TextCommand,
)
from discord.ext.commands import (
    Context,
)
from discord.ext.commands import (
    check as text_check,
)
from discord.interactions import Interaction

from bot.errors import InvalidAuthorizationError

if TYPE_CHECKING:
    from bot.client import Phoenix

    Info = Context[Phoenix] | Interaction[Phoenix]
    CheckPredicate = Union[
        Callable[[Info], bool], Callable[[Info], Coroutine[Any, Any, bool]]
    ]
    Checkable = Union[SlashCommand, ContextMenu, TextCommand]


def combined_check(predicate: "CheckPredicate") -> Any:
    """Build a check that functions for both application and text commands."""

    def decorate(func: "Checkable") -> Any:
        if isinstance(func, SlashCommand):
            slash_check(predicate)(func)

        elif isinstance(func, TextCommand):
            text_check(predicate)(func)

        else:
            slash_check(predicate)(func)
            text_check(predicate)(func)

        return func

    return decorate


def bot_dev() -> Any:
    """Check if the command invoker is a bot dev."""

    async def predicate(info: "Info") -> bool:
        user = info.user if isinstance(info, Interaction) else info.author

        if user.id == 229779964898181120:
            return True

        raise InvalidAuthorizationError

    return combined_check(predicate)


def block() -> Any:
    """Cause a check failure."""

    def predicate(info: "Info") -> bool:
        raise InvalidAuthorizationError

    return combined_check(predicate)
