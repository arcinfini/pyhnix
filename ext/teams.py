import typing, enum, logging
from collections import OrderedDict

from discord.ext import commands
from discord import app_commands, Interaction
import discord, asyncpg


from internal import app_errors, client

logger = logging.getLogger(__name__)

"""
team create
team members [add/remove] @member teamname

team info teamname
team edit teamname

"""

class MemberAction(enum.Enum):
    add = 0
    remove = 1

class Team:
    """
    CREATE TABLE team (
        id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
        guildid BIGINT NOT NULL,
        name VARCHAR(50) NOT NULL,
        lead_roleid BIGINT,
        member_roleid BIGINT,

        UNIQUE(guildid, name)
    )
    """

    def __init__(self, team_cache, /, data):
        self.name = data.get('name', None)
        self.guildid = data.get('guildid', None)

        self.id = data.get('id', None)

        self.lead_roleid = data.get('lead_roleid', None)
        self.member_roleid = data.get('member_roleid', None)

        self.team_cache = team_cache

    def __eq__(self, other):
        """
        Ensures both objects have the same name and guild id
        """
        
        return self.id == other.id

    def __repr__(self):
        
        return f"<Team name={self.name}, lead_id={self.lead_roleid}>"

    async def define_info(self) -> str:
        """
        TODO
        Defines a string to display basic information about the team.

        Displays, team id, team name, lead roleid, member roleid and stored
        member count
        """

        async with self.team_cache.bot.database.acquire() as conn:
            member_count = await conn.fetchval("""
                SELECT COUNT(userid) 
                FROM team_member 
                WHERE teamid=$1
                GROUP BY teamid;
                """, self.id
            )

            if member_count is None: member_count = 0

        return f"```"+\
            f"Team: {self.name}\n"+\
            f"Lead: {self.lead_roleid}\n"+\
            f"Role: {self.member_roleid}\n"+\
            f"Member Count: {member_count}\n"+\
            "```"

    async def fetch_members(self) -> typing.List[int]:
        """
        Returns a list of members that are currently a part of the team
        """

        async with self.team_cache.bot.database.acquire() as conn:
            members = await conn.fetch("""
            SELECT userid 
            FROM team_member
            WHERE teamid = $1
            """, self.id)

        return [m['userid'] for m in members]

    async def add_member(self, user: discord.User):
        """
        Adds a guild member to the team members
        """

        logger.debug("add %d to %s", user.id, repr(self))

        async with self.team_cache.bot.database.acquire() as conn:
            await conn.execute("""
            INSERT INTO team_member (teamid, userid)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING;
            """, self.id, user.id)

    async def remove_member(self, user: discord.User):
        """
        Removes a user from the team members
        """

        logger.debug("remove %d from %s", user.id, repr(self))

        async with self.team_cache.bot.database.acquire() as conn:
            await conn.execute("""
            DELETE FROM team_member
            WHERE teamid = $1 AND userid = $2;
            """, self.id, user.id)
        

    async def edit(
        self, 
        *, 
        name:typing.Optional[str]=None,
        lead_role: typing.Optional[discord.Role]=None, 
        member_role: typing.Optional[discord.Role]=None
    ):
        """
        Edits the database to reflect the changes

        Makes used of coalesce which returns the first non-null value. This
        should allow the passing of default values without the need to overwrite
        """
        
        logger.debug("update team %s", repr(self))

        lead_roleid = lead_role.id if lead_role is not None else None
        member_roleid = member_role.id if member_role is not None else None

        async with self.team_cache.bot.database.acquire() as conn:
            updated = await conn.fetchrow("""
            UPDATE team SET
                name = COALESCE($1, name),
                lead_roleid = COALESCE($2, lead_roleid),
                member_roleid = COALESCE($3, member_roleid)
            WHERE id = $4
            RETURNING *
            """, name, lead_roleid, member_roleid, self.id)

            self.raw_edit(
                name=updated['name'], 
                lead_roleid=updated['lead_roleid'],
                member_roleid=updated['member_roleid']
            )

    def raw_edit(
        self,
        *,
        name:typing.Optional[str] = None,
        lead_roleid: typing.Optional[int] = None,
        member_roleid: typing.Optional[int] = None
    ):
        """
        A currently unimplemented method for editing the internal attributes of
        a team without making any database calls.

        This is to be used by the Cache to update teams in force_fetch
        """

        if name is not None: self.name = name
        if lead_roleid is not None: self.lead_roleid = lead_roleid
        if member_roleid is not None: self.member_roleid = member_roleid

    async def delete(self):
        """
        Deletes the role from the internal database
        """

        logger.debug("delete team %s", repr(self))

        async with self.team_cache.bot.database.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM team
                WHERE id = $1
                """, self.id
            )

T = typing.TypeVar("T")
class LRUCache(typing.Generic[T]):
    """
    A least recently used cache implemented to lower the database calls with the
    team commands
    """

    def __init__(self, *, limit:int=128):
        self.__limit = limit
        self.__cache = OrderedDict()

    def put(self, key, value:T):
        self.__cache[key] = value
        self.__cache.move_to_end(key)

        if len(self.__cache) > self.__limit:
            self.__cache.popitem(last= False)

    def get(self, key) -> typing.Optional[T]:
        value = self.__cache.get(key, None)
        if value is None: return None

        self.__cache.move_to_end(key)
        return value

Teams = typing.Dict[str, Team]

class GuildTeamsCache(LRUCache[Teams]):
    """
    Contains an LRU Cache of all teams within a guild

    Current issues arise when a guild is in the cache and the database is
    updated
    """

    def __init__(self, bot: client.Phoenix):
        super().__init__()

        self.bot = bot

    def _put_team_if_cache(self, team:Team):
        """
        Takes a Team and puts it inside the cache if a cache dict exists for the
        guild of the team
        """

        value = self.get(team.guildid)
        if value is None: return

        value.update({team.name:team})

    async def fetch(self, guild: discord.Guild) -> Teams:
        """
        Returns the teams belonging to the given guild
        """
        value = self.get(guild.id)
        if value is not None: return value

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
                """, guild.id
            )

        # TODO: smarter iteration over existing items to raw_edit attributes
        teams = {record['name']:Team(self, record) for record in result}
        self.put(guild.id, teams)

        return teams

    async def create_team(
        self, guild:discord.Guild, *, 
        name:str, 
        lead_role:discord.Role, 
        member_role:discord.Role
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
                name, guild.id, lead_role.id, member_role.id
            )

        team = Team(self, record)
        self._put_team_if_cache(team)

        logger.debug("Team created %s", repr(team))
        
        return team

@app_commands.guild_only
@app_commands.default_permissions(manage_roles=True)
class Main(app_commands.Group):

    class TeamTransformer(app_commands.Transformer):
        async def transform(self, interaction: Interaction, value:str) -> Team:
            """
            Converts the value (team name) into a team. Makes use of force_fetch
            to ensure the up-to-date database values are used
            """
            
            teams = await Main.teams.force_fetch(interaction.guild)
            team = teams.get(value)

            if team is None:
                raise app_errors.TransformationError(
                    "Team with name '%s' not found in database" % value
                )

            return team

        async def autocomplete(self, interaction: Interaction, value:str):
            """
            Returns an `app_commands.Choice` object with choices of the teams in
            the guild the autocomplete is being used in
            """
            
            teams = await Main.teams.fetch(interaction.guild)
            contains = lambda x: value in x
            x = lambda k: app_commands.Choice(name=k, value=k)
            return [x(value) for value in filter(contains, teams.keys())]

    def __init__(self, bot):
        super().__init__(name="team")

        self.bot = bot
        Main.teams = GuildTeamsCache(bot)

    async def team_info(self, team: Team):
        embed = discord.Embed(
            title="Team Info",
            description=await team.define_info()
        )

        return embed

    def can_administrate_teams(self, member: discord.Member):
        """
        Checks if the member is an administrator
        """
        
        return member.guild_permissions.administrator

    def can_control_team(self, member: discord.Member, team: Team):
        """
        Checks if the member is an administrator or if they have the respective
        team lead role
        """
        
        return team.lead_roleid in [r.id for r in member.roles] \
            or self.can_administrate_teams(member)

    async def interaction_check(self, interaction: Interaction):
        """
        member needs to have manage role permissions or administrator
        or to have the team lead role of the team they are attempting to manage
        
        the bot also needs to have the ability to manage roles
        """
        return True

    @app_commands.command(name="create")
    @app_commands.describe(
        name="The name of the team",
        lead="The role that corresponds to the team lead",
        role="The role that is given to members of the team"
    )
    async def _create(
        self, 
        interaction: Interaction, 
        name: str, 
        lead: discord.Role, 
        role: discord.Role
    ):
        """
        Creates a new team for the guild
        """
        if not self.can_administrate_teams(interaction.user):

            raise app_errors.ClearanceError(
                "You do not have proper clearance to use this command"
            )

        try:
            team = await self.teams.create_team(
                interaction.guild, 
                name=name, 
                lead_role=lead, 
                member_role=role
            )

            await interaction.response.send_message(f"{team.name} was created")
        except asyncpg.UniqueViolationError as e:

            await interaction.response.send_message(
                f"A team with name `{name}` already exists in this server"
            )

    @app_commands.command(name="delete")
    @app_commands.describe(
        team="The name of the team"
    )
    async def _delete(
        self, 
        interaction: Interaction, 
        team: app_commands.Transform[Team, TeamTransformer]
    ):
        """
        Deletes a team from the guild. Asks for clarification. 
        Can only be done by server administrators
        """

        if not self.can_administrate_teams(interaction.user):

            raise app_errors.ClearanceError(
                "You do not have proper clearance to use this command"
            )

        await team.delete()

        await interaction.response.send_message(f"{team.name} was deleted")

    @app_commands.command(name="edit")
    @app_commands.describe(
        team="The name of the team",
        name="The new name to give to the team",
        lead="The new role to correspond to the team lead",
        role="The new role that is given to members of the team"
    )
    async def _edit(
        self, 
        interaction: Interaction, 
        team: app_commands.Transform[Team, TeamTransformer],
        lead: typing.Optional[discord.Role],
        role: typing.Optional[discord.Role],
        name: typing.Optional[str]
    ):
        """
        Edits a team's properties.
        Can only be done by server administrators
        """

        if not self.can_administrate_teams(interaction.user):

            raise app_errors.ClearanceError(
                "You do not have proper clearance to use this command"
            )

        await interaction.response.defer()

        await team.edit(name=name, lead_role=lead, member_role=role)
        # TODO: update member roles to new role

        await interaction.followup.send(
            f"{team.name} updated | new team info",
            embed=await self.team_info(team)
        )

    @app_commands.command(name="members")
    @app_commands.describe(
        team="The name of the team to add",
        user="The user to manage",
        action="The action to take on the user"
    )
    async def _members(
        self, 
        interaction: Interaction,
        action: MemberAction,
        user: discord.User,
        team: app_commands.Transform[Team, TeamTransformer]
    ):
        """
        Adds or removes a member from the list of team members. Must be done by
        a team lead or a member with administrative permissions.
        """

        if not self.can_control_team(interaction.user, team):

            raise app_errors.ClearanceError(
                "You do not have proper clearance to use this command"
            )

        # member fetch may be redundant
        member = await interaction.guild.fetch_member(user.id)

        if action == MemberAction.add:
            
            await team.add_member(member)

            await member.add_roles(
                discord.Object(team.member_roleid), 
                reason="add to team"
            )

            await interaction.response.send_message(
                f"{member.mention} added to {team.name}",
                allowed_mentions=None,
                ephemeral=True
            )
            return
        
        elif action == MemberAction.remove:
            
            await team.remove_member(user)
            
            if member is not None:
                await member.remove_roles(
                    discord.Object(team.member_roleid), 
                    reason="remove from team"
                )

            await interaction.response.send_message(
                f"{user.mention} removed from {team.name}",
                allowed_mentions=discord.AllowedMentions.none(),
                ephemeral=True
            )
            return

    @app_commands.command(name="list")
    async def _list(
        self, 
        interaction: Interaction
    ):
        """
        Lists all the teams and short info of the guild
        """
        if not self.can_administrate_teams(interaction.user):

            raise app_errors.ClearanceError(
                "You do not have proper clearance to use this command"
            )

        teams = await self.teams.force_fetch(interaction.guild)

        embed = discord.Embed(title="Team List")
        for team in teams.values():
            embed.add_field(
                name=team.name, 
                value=await team.define_info(),
                inline=True
            )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(name="info")
    @app_commands.describe(
        team="The name of the team"
    )
    async def _info(
        self, 
        interaction: Interaction, 
        team: app_commands.Transform[Team, TeamTransformer]
    ):
        """
        Provides info about the given team.
        """

        if not self.can_control_team(interaction.user, team):

            raise app_errors.ClearanceError(
                "You do not have proper clearance to use this command"
            )

        await interaction.response.send_message(
            embed=await self.team_info(team),
            ephemeral=True
        )

    @app_commands.command(name="memberlist")
    async def _memberlist(
        self, 
        interaction: Interaction, 
        team: app_commands.Transform[Team, TeamTransformer]
    ):
        """
        Provides a list of members that belong to the team
        """

        if not self.can_control_team(interaction.user, team):

            raise app_errors.ClearanceError(
                "You do not have proper clearance to use this command"
            )

        members = [f"<@{m}>" for m in await team.fetch_members()]
        
        result = ", ".join(members)
        await interaction.response.send_message(
            result, ephemeral=True
        )



async def setup(bot):
    bot.tree.add_command(Main(bot))

    logger.info("%s initialized", __name__)