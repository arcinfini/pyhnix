import typing, logging

import discord

from . import Team
from internal import client
from internal.utils import LRUCache

logger = logging.getLogger(__name__)

Teams = typing.Dict[str, Team]


class GuildTeamsCache(LRUCache[Teams]):
    """
    Contains an LRU Cache of all teams within a guild

    Current issues arise when a guild is in the cache and the database is
    updated
    """

    def __init__(self, bot: client.Phoenix):
        super().__init__()

        self.bot: client.Phoenix = bot

    def _put_team_if_cache(self, team: Team):
        """
        Takes a Team and puts it inside the cache if a cache dict exists for the
        guild of the team
        """

        value = self.get(team.guildid)
        if value is None:
            return

        value.update({team.name: team})

    async def fetch(self, guild: discord.Guild) -> Teams:
        """
        Returns the teams belonging to the given guild
        """
        value = self.get(guild.id)
        if value is not None:
            return value

        teams = await self.force_fetch(guild)

        return teams

    async def force_fetch(self, guild: discord.Guild) -> Teams:
        """
        Forces a fetch of the database to update the cache
        """

        logger.debug("force_fetch used for %d", guild.id)

        async with self.bot.database.acquire() as conn:
            result = await conn.fetch(
                """
                SELECT * 
                FROM team
                WHERE guildid = $1
                """,
                guild.id,
            )

        # TODO: smarter iteration over existing items to raw_edit attributes
        teams = {record["name"]: Team(self, record) for record in result}
        self.put(guild.id, teams)

        return teams

    async def create_team(
        self,
        guild: discord.Guild,
        *,
        name: str,
        lead_role: discord.Role,
        member_role: discord.Role,
    ) -> Team:
        """
        Creates a new team inside the database and returns a class
        representation of the team.

        Raises asyncpg.UniqueViolationError if the team already exists
        """

        async with self.bot.database.acquire() as conn:
            record = await conn.fetchrow(
                """
                INSERT INTO team (name, guildid, lead_roleid, member_roleid)
                VALUES ($1, $2, $3, $4)
                RETURNING *;
                """,
                name,
                guild.id,
                lead_role.id,
                member_role.id,
            )

        team = Team(self, record)
        self._put_team_if_cache(team)

        logger.debug("Team created %s", repr(team))

        return team
