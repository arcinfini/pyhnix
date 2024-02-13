from typing import TYPE_CHECKING, TypedDict

from discord.ext.commands import Context as _Context
from discord.interactions import Interaction as _Interaction

if TYPE_CHECKING:
    from bot.client import Phoenix

    Interaction = _Interaction[Phoenix]
    Context = _Context[Phoenix]

__all__ = ("Context", "Interaction", "TeamData")


class TeamData(TypedDict):
    """A representation of a team stored in the database."""

    name: str
    guild_id: int
    id: int
    lead_role_id: int
    member_role_id: int
