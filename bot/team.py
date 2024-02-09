import logging
from typing import Optional, TYPE_CHECKING

import discord

from bot.database import Database
from bot.utils import Cache

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from bot.utils.types import TeamData


class Team:
    """An object of a team."""

    __slots__ = (
        "name",
        "guild_id",
        "id",
        "lead_role_id",
        "member_role_id",
        "__database",
    )

    if TYPE_CHECKING:
        name: str
        guild_id: int
        id: int
        lead_role_id: int
        member_role_id: int
        __database: Database

    def __init__(self, database: Database, /, data: "TeamData"):
        self._update(data)
        self.__database = database

    def __eq__(self, other: object) -> bool:
        """Ensure both teams have the same id."""
        if not isinstance(other, Team):
            return False

        return self.id == other.id

    def __repr__(self) -> str:
        """Define object representation."""
        return f"<Team name={self.name}, lead_id={self.lead_role_id}>"

    async def define_info(self) -> str:
        """Build a string to display basic information about the team.

        Displays team id, team name, lead roleid, member roleid and stored
        member count.
        """
        member_count = len(await self.fetch_members())

        return (
            "```"
            f"Team: {self.name}\n"
            f"Lead: {self.lead_role_id}\n"
            f"Role: {self.member_role_id}\n"
            f"Member Count: {member_count}\n"
            "```"
        )

    async def fetch_members(self) -> list[int]:
        """Return a list of user ids that are currently a member of the team."""
        return await self.__database.fetch_members_from_team(self.id)

    async def add_member(
        self, user: discord.Object | discord.User | discord.Member
    ) -> None:
        """Add a user to the team members."""
        await self.__database.add_member_to_team(self.id, user.id)

    async def remove_member(
        self, user: discord.Object | discord.User | discord.Member
    ) -> None:
        """Remove a user from the team members."""
        await self.__database.remove_member_from_team(self.id, user.id)

    async def edit(
        self,
        *,
        name: Optional[str] = None,
        lead_role: Optional[discord.Role] = None,
        member_role: Optional[discord.Role] = None,
    ) -> None:
        """Edit the team's attributes and update database."""
        lead_role_id = lead_role.id if lead_role is not None else None
        member_role_id = member_role.id if member_role is not None else None

        data = await self.__database.update_team(
            self.id,
            name=name,
            lead_role_id=lead_role_id,
            member_role_id=member_role_id,
        )

        self._update(data)

    def _update(
        self,
        /,
        data: "TeamData",
    ) -> None:
        """Edit the internal cache without updating the database."""
        self.name = data["name"]
        self.id = data["id"]

        self.guild_id = data["guild_id"]
        self.lead_role_id = data["lead_role_id"]
        self.member_role_id = data["member_role_id"]

    async def delete(self) -> None:
        """Delete the team from the internal database."""
        await self.__database.delete_team(self.id)


class TeamGuild:
    """A guild that contains teams."""

    def __init__(self, database: Database, /, guild: discord.Guild) -> None:
        self.__database = database
        self.guild = guild
        self.__cache: Cache[int, Team] = Cache()

    async def create_team(
        self, name: str, lead_role: discord.Role, member_role: discord.Role
    ) -> Team:
        """Create a team with the provided parameters."""
        data = await self.__database.create_team(
            self.guild.id, name, lead_role.id, member_role.id
        )

        team = Team(self.__database, data=data)
        self.__cache.put(team.id, team)

        return team

    def get_team(self, id: int) -> Optional[Team]:
        """Get the team with the provided id if stored in the internal cahce."""
        return self.__cache.get(id)

    async def fetch_team(self, id: int) -> Optional[Team]:
        """Fetch the team with the provided id."""
        data = await self.__database.fetch_team(id)
        if data is None:
            return None

        team = Team(self.__database, data=data)
        self.__cache.put(team.id, team)
        return team

    async def fetch_teams(self) -> list[Team]:
        """Fetch all the teams in the guild."""
        entries = await self.__database.fetch_teams_from_guild(self.guild.id)

        teams = []

        for data in entries:
            team = Team(self.__database, data=data)
            self.__cache.put(team.id, team)
            teams.append(team)

        return teams
