import logging
from typing import Optional, cast

import asyncpg

from bot.utils.types import TeamData

_log = logging.getLogger(__name__)


class Database:
    """A pooled database connection with predefined queries."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self.__pool = pool

    async def close(self) -> None:
        """Close the pool connection."""
        await self.__pool.close()

    async def fetch_members_from_team(self, id: int) -> list[int]:
        """Select a list of member ids within a team."""
        _log.debug("fetch members in %d", id)
        query = """
            SELECT user_id
            FROM team_member
            WHERE team_id = $1
        """

        conn = self.__pool
        members = await conn.fetch(
            query,
            id,
        )

        return [m["user_id"] for m in members]

    async def add_member_to_team(self, team_id: int, user_id: int) -> None:
        """Insert a user id into a team."""
        _log.debug("add %d to %d", user_id, team_id)
        query = """
            INSERT INTO team_member (team_id, user_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING;
        """

        conn = self.__pool
        await conn.execute(query, team_id, user_id)

    async def remove_member_from_team(self, team_id: int, user_id: int) -> None:
        """Remove a user id from a team."""
        _log.debug("remove %d from %d", user_id, team_id)
        query = """
            DELETE FROM team_member
            WHERE team_id = $1 AND user_id = $2;
        """

        conn = self.__pool
        await conn.execute(
            query,
            team_id,
            user_id,
        )

    async def update_team(
        self,
        id: int,
        /,
        lead_role_id: Optional[int] = None,
        member_role_id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> TeamData:
        """Update a team's values.

        Makes used of coalesce which returns the first non-null value. This
        should allow the passing of default values without the need to overwrite
        """
        query = """
            UPDATE team SET
                name = COALESCE($1, name),
                lead_role_id = COALESCE($2, lead_role_id),
                member_role_id = COALESCE($3, member_role_id)
            WHERE id = $4
            RETURNING *
        """

        conn = self.__pool
        data = await conn.fetchrow(
            query,
            name,
            lead_role_id,
            member_role_id,
            id,
        )

        return cast(TeamData, data)

    async def delete_team(self, id: int) -> None:
        """Delete a team from the database."""
        _log.debug("delete team %s", repr(self))
        query = """
            DELETE FROM team
            WHERE id = $1
        """

        conn = self.__pool
        await conn.execute(query, id)

    async def create_team(
        self, guild_id: int, name: str, lead_role_id: int, member_role_id: int
    ) -> TeamData:
        """Create a team within the database and return the created data."""
        query = """
            INSERT INTO team (name, guild_id, lead_role_id, member_role_id)
            VALUES ($1, $2, $3, $4)
            RETURNING *;
        """

        conn = self.__pool
        data = await conn.fetchrow(
            query,
            name,
            guild_id,
            lead_role_id,
            member_role_id,
        )

        return cast(TeamData, data)

    async def fetch_team(self, id: int) -> Optional[TeamData]:
        """Return possible data for a team."""
        query = """
            SELECT *
            FROM team
            WHERE id = $1
        """

        conn = self.__pool
        data = await conn.fetch(
            query,
            id,
        )

        return cast(TeamData, data)

    async def fetch_teams_from_guild(self, guild_id: int) -> list[TeamData]:
        """Return a list of teams related to a guild."""
        query = """
            SELECT *
            FROM team
            WHERE guild_id = $1
        """

        conn = self.__pool
        entries = await conn.fetch(
            query,
            guild_id,
        )

        return [cast(TeamData, data) for data in entries]
