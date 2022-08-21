import typing, enum, logging
from collections import OrderedDict

from discord.ext import commands
from discord import app_commands, Interaction
import discord

from internal import app_errors

logger = logging.getLogger(__name__)

"""
team create
team members [add/remove] @member teamname

team info teamname
team edit teamname

"""

"""
TLDRTODO

1. update instead of replace teams on force_fetch
2. ~~implement team.edit~~
3. ~~implement team.raw_edit~~
4. ~~implement team.delete()~~
5. add ephemeral tags to responses
6. finish team_info stub
7. ~~implement command permission checks~~

"""

class MemberAction(enum.Enum):
    add = 0
    remove = 1

class Team:
    """
    name string
    
    guildid bigint
    lead_roleid bigint
    member_roleid bigint

    members bigint[]

    unique (name, guildid)
    """

    def __init__(self, team_cache, name:str, guildid:int, /, data):
        self.name = name
        self.guildid = guildid

        self.lead_roleid = data.get('lead_roleid', None)
        self.member_roleid = data.get('member_roleid', None)
        self.members:list = data.get('members', [])

        self.team_cache = team_cache

    @classmethod
    def from_record(cls, team_cache, record):
        
        return cls(team_cache, record.get('name'), record.get('guildid'), record)

    def __eq__(self, other):
        """
        Ensures both objects have the same name and guild id
        """
        # inconsistencies can arise if the cache fails to update an existing
        # team's properties TODO: solution rather than overwriting exisiting
        # teams, update the internal attributes
        
        return self.name == other.name and self.guildid == other.guildid

    def __str__(self):
        return "```\n" +\
            f"Team: {self.name}\n" +\
            f"Lead: {self.lead_roleid}\n" +\
            f"Role: {self.member_roleid}\n" +\
            f"Members: {len(self.members)}\n" +\
            "```"

    async def add_member(self, member: discord.Member):
        """
        Adds a guild member to the team members
        """

        # check if member is already in the members list
        # add member to team members list
        if member.id in self.members: return

        self.members.append(member.id)

        async with self.team_cache.bot.database.acquire() as conn:
            await conn.execute("""
            update esports_teams set 
                members = array_append(members, $1)
            where name = $2 and guildid = $3
            """, member.id, self.name, self.guildid)

    async def remove_member(self, member: discord.User):
        """
        Removes a user from the team members
        """

        # check if part of team members list
        # if so remove from team members list
        if member.id in self.members:
            self.members.remove(member.id)

            async with self.team_cache.bot.database.acquire() as conn:
                await conn.execute("""
                update esports_teams set 
                    members = array_remove(members, $1)
                where name = $2 and guildid = $3
                """, member.id, self.name, self.guildid)
        

    async def edit(
        self, 
        *, 
        name:str=None,
        lead_role: discord.Role=None, 
        member_role: discord.Role=None
    ):
        """
        Edits the database to reflect the changes

        Makes used of coalesce which returns the first non-null value. This
        should allow the passing of default values without the need to overwrite
        """

        async with self.team_cache.bot.database.acquire() as conn:
            await conn.execute("""
            update esports_teams set
                name = COALESCE($1, name)
                lead_roleid = COALESCE($2, lead_roleid)
                member_roleid = COALESCE($3, member_roleid)
            where name = $4 and guildid = $5
            """, name, lead_role.id, member_role.id, self.name, self.guildid)

            self.raw_edit(
                name=name, 
                lead_roleid=lead_role.id,
                member_roleid=member_role.id
            )

    def raw_edit(
        self,
        *,
        name:str = None,
        lead_roleid: int = None,
        member_roleid: int = None,
        members: typing.List[int] = None
    ):
        """
        A currently unimplemented method for editing the internal attributes of
        a team without making any database calls.

        This is to be used by the Cache to update teams in force_fetch
        """

        if name is not None: self.name = name
        if lead_roleid is not None: self.lead_roleid = lead_roleid
        if member_roleid is not None: self.member_roleid = member_roleid
        if members is not None: self.members = members

    async def delete(self):
        """
        Deletes the role from the internal database
        """

        async with self.team_cache.bot.database.acquire() as conn:
            await conn.execute("""
            delete from esports_teams
            where name = $1 and guildid = $2
            """, self.name, self.guildid)

T = typing.TypeVar("T")
class LRUCache(typing.Generic[T]):

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

    def __init__(self, bot):
        super().__init__()

        self.bot = bot

    async def fetch(self, guild: discord.Guild) -> Teams:
        """
        Returns the teams belonging to the given guild
        """
        value = self.get(guild.id)
        if value is not None: return value

        logger.debug("Fetch teams for %d", guild.id)

        teams = await self.force_fetch(guild)

        return teams

    async def force_fetch(self, guild: discord.Guild) -> Teams:
        """
        Forces a fetch of the database to update the cache
        """

        logger.debug("force_fetch used")

        async with self.bot.database.acquire() as conn:
            result = await conn.fetch("""
            select * from esports_teams where guildid=$1
            """, guild.id)

        # TODO: smarter iteration over existing items to raw_edit attributes
        teams = {record['name']:Team.from_record(self, record) for record in result}
        self.put(guild.id, teams)

        return teams

    async def create_team(
        self, guild:discord.Guild, *, 
        name:str, 
        lead_role:discord.Role, 
        member_role:discord.Role
    ) -> Team:
        """
        Updates the internal cache to validate a team with the name and guild
        does not already exist and inserts a new team into the database and 
        cache.
        """
        
        teams = await self.force_fetch(guild)

        # there can be situations where another process creates a team during
        # this frame with the same name and guild; chances are unlikely but it
        # should be kept in mind

        if teams.get(name) is not None:
            raise ValueError('Attempt to create a team with a name that already exists')

        async with self.bot.database.acquire() as conn:
            await conn.execute("""
            insert into esports_teams (name, guildid, lead_roleid, member_roleid, members)
            values ($1, $2, $3, $4, $5)
            """, name, guild.id, lead_role.id, member_role.id, [])

        team = Team.from_record(self, {
            'name':name,
            'guildid': guild.id,
            'lead_roleid': lead_role.id,
            'member_roleid': member_role.id,
            'members': []
        })
        teams.update({team.name:team})
        
        return team

@app_commands.guild_only
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
                raise ValueError("Team '{}' not found in database" % value)

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

    def team_info(self, team: Team):
        embed = discord.Embed(
            title="Team Info",
            description=str(team)
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

        team = await self.teams.create_team(
            interaction.guild, 
            name=name, 
            lead_role=lead, 
            member_role=role
        )

        await interaction.response.send_message(f"{team.name} was created")

    @app_commands.command(name="delete")
    async def _delete(self, interaction: Interaction, team: TeamTransformer):
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
    async def _edit(
        self, 
        interaction: Interaction, 
        team: TeamTransformer,
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
            embed=self.team_info(team)
        )

    @app_commands.command(name="members")
    async def _members(
        self, 
        interaction: Interaction,
        action: MemberAction,
        user: discord.User,
        team: TeamTransformer
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
                allowed_mentions=None
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
                allowed_mentions=None
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
        for team in teams:
            embed.add_field(name=team.name, value=str(team), inline=True)

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(name="info")
    async def _info(self, interaction: Interaction, team: TeamTransformer):
        """
        Provides info about the given team.
        """

        if not self.can_control_team(interaction.user, team):

            raise app_errors.ClearanceError(
                "You do not have proper clearance to use this command"
            )

        await interaction.response.send_message(
            embed=self.team_info(team),
            ephemeral=True
        )


async def setup(bot):
    bot.tree.add_command(Main(bot))

    logger.info("%s initialized", __name__)