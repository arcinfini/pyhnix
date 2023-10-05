import typing, enum, logging

from discord.ext import commands
from discord import app_commands, Interaction
import discord.ui as dui
import discord, asyncpg


from internal import client, errors
from internal.utils import GuildInteraction

from internal.teams import Team, GuildTeamsCache


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
    edit = 2


class TeamUserEditView(dui.View):
    def __init__(self, team):
        super().__init__()
        self.team = team

    @dui.select(cls=dui.UserSelect, min_values=0, max_values=10)
    async def _user_select(
        self, interaction: Interaction, select: dui.UserSelect
    ):
        """
        The select provided in the team user editor view. This does not respond
        and is instead used in the button codes.
        """

        await interaction.response.defer(thinking=False)

    @dui.button(label="Add to team")
    async def _add_team(self, interaction: Interaction, button: dui.Button):
        """
        The button provided in the team user editor view that adds the selected
        members to the team. This iterates over the selected members and both
        adds them to the team in the database and gives them the team role
        """

        await interaction.response.defer(ephemeral=True)

        for member in self._user_select.values:
            if not isinstance(member, discord.Member):
                raise errors.InvalidInvocationError(
                    content="This command is returning a user rather than a \
                        server member"
                )

            if member.get_role(self.team.member_roleid) is not None:
                continue

            await self.team.add_member(member)
            await member.add_roles(
                discord.Object(self.team.member_roleid), reason="add to team"
            )

        await interaction.followup.send("Members edited", ephemeral=True)

    @dui.button(label="Remove from Team")
    async def _remove_team(self, interaction: Interaction, button: dui.Button):
        """
        The button provided in the team user editor view that removes the
        selected members to the team. This iterates over the selected members
        and both removes them from the team in the database and removes the team
        role from them
        """

        await interaction.response.defer(ephemeral=True)

        for member in self._user_select.values:
            if not isinstance(member, discord.Member):
                raise errors.InvalidInvocationError(
                    content="This command is returning a user rather than a \
                        server member"
                )

            if member.get_role(self.team.member_roleid) is None:
                continue

            await self.team.remove_member(member)
            await member.remove_roles(
                discord.Object(self.team.member_roleid),
                reason="remove from team",
            )

        await interaction.followup.send("Members edited", ephemeral=True)


class TeamTransformer(app_commands.Transformer):
    async def transform(
        self, interaction: GuildInteraction, value: str
    ) -> Team:
        """
        Converts the value (team name) into a team. Makes use of force_fetch
        to ensure the up-to-date database values are used
        """

        teams = await Main.teams.force_fetch(interaction.guild)
        team = teams.get(value)

        if team is None:
            raise errors.TransformationError(
                content="Team with name '%s' not found in database" % value
            )

        return team

    async def autocomplete(self, interaction: GuildInteraction, value: str):
        """
        Returns an `app_commands.Choice` object with choices of the teams in
        the guild the autocomplete is being used in
        """

        teams = await Main.teams.fetch(interaction.guild)
        contains = lambda x: value in x
        x = lambda k: app_commands.Choice(name=k, value=k)
        return [x(value) for value in filter(contains, teams.keys())]


@app_commands.default_permissions(manage_roles=True)
class Main(commands.Cog, name="Teams"):
    def __init__(self, bot: client.Phoenix):
        self.bot = bot
        Main.teams = GuildTeamsCache(bot)

    async def team_info(self, team: Team) -> discord.Embed:
        """
        Creates a simple embed of team info to return
        """

        embed = discord.Embed(
            title="Team Info", description=await team.define_info()
        )

        return embed

    def can_administrate_teams(self, member: discord.Member) -> bool:
        """
        Checks if the member is an administrator and therefore can administrate
        teams
        """

        return member.guild_permissions.administrator

    def can_control_team(self, member: discord.Member, team: Team) -> bool:
        """
        Checks if the member is an administrator or if they have the respective
        team lead role
        """

        return team.lead_roleid in [
            r.id for r in member.roles
        ] or self.can_administrate_teams(member)

    async def interaction_check(self, interaction: Interaction):
        """
        member needs to have manage role permissions or administrator
        or to have the team lead role of the team they are attempting to manage

        the bot also needs to have the ability to manage roles
        """
        return True

    team = app_commands.Group(
        name="team",
        description="Edits and manages teams",
        guild_only=True,
    )

    @team.command(name="clean")
    async def _clean(
        self,
        interaction: Interaction,
        team: app_commands.Transform[Team, TeamTransformer],
    ):
        """
        Retreives all the members of a team and removes them from it
        """

        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_administrate_teams(interaction.user):
            raise errors.ClearanceError(
                content="You do not have proper clearance to use this command"
            )

        failed = []

        await interaction.response.defer(ephemeral=True)

        mem_ids = await team.fetch_members()
        for member_id in mem_ids:
            try:
                await team.remove_member(discord.Object(member_id))

                member = await interaction.guild.fetch_member(member_id)
                await member.remove_roles(discord.Object(team.member_roleid))
            except:
                failed.append(member_id)

        failed_for = [f"<@{id}>" for id in failed]
        await interaction.edit_original_response(
            content=f"Completed interaction\nFailed for {failed_for}"
        )

    @team.command(name="create")
    @app_commands.describe(
        name="The name of the team",
        lead="The role that corresponds to the team lead",
        role="The role that is given to members of the team",
    )
    async def _create(
        self,
        interaction: Interaction,
        name: str,
        lead: discord.Role,
        role: discord.Role,
    ):
        """
        Creates a new team for the guild
        """

        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_administrate_teams(interaction.user):
            raise errors.ClearanceError(
                content="You do not have proper clearance to use this command"
            )

        try:
            team = await self.teams.create_team(
                interaction.guild, name=name, lead_role=lead, member_role=role
            )

            await interaction.response.send_message(f"{team.name} was created")
        except asyncpg.UniqueViolationError as e:
            await interaction.response.send_message(
                f"A team with name `{name}` already exists in this server"
            )

    @team.command(name="delete")
    @app_commands.describe(team="The name of the team")
    async def _delete(
        self,
        interaction: Interaction,
        team: app_commands.Transform[Team, TeamTransformer],
    ):
        """
        Deletes a team from the guild. Asks for clarification.
        Can only be done by server administrators
        """

        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_administrate_teams(interaction.user):
            raise errors.ClearanceError(
                content="You do not have proper clearance to use this command"
            )

        await team.delete()

        await interaction.response.send_message(f"{team.name} was deleted")

    @team.command(name="edit")
    @app_commands.describe(
        team="The name of the team",
        name="The new name to give to the team",
        lead="The new role to correspond to the team lead",
        role="The new role that is given to members of the team",
    )
    async def _edit(
        self,
        interaction: Interaction,
        team: app_commands.Transform[Team, TeamTransformer],
        lead: typing.Optional[discord.Role],
        role: typing.Optional[discord.Role],
        name: typing.Optional[str],
    ):
        """
        Edits a team's properties.
        Can only be done by server administrators
        """

        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_administrate_teams(interaction.user):
            raise errors.ClearanceError(
                content="You do not have proper clearance to use this command"
            )

        await interaction.response.defer()

        await team.edit(name=name, lead_role=lead, member_role=role)
        # TODO: update member roles to new role

        await interaction.followup.send(
            f"{team.name} updated | new team info",
            embed=await self.team_info(team),
        )

    @team.command(name="members")
    @app_commands.describe(
        team="The name of the team to add",
        user="The user to manage",
        action="The action to take on the user",
    )
    async def _members(
        self,
        interaction: Interaction,
        action: MemberAction,
        user: discord.User,
        team: app_commands.Transform[Team, TeamTransformer],
    ):
        """
        Adds or removes a member from the list of team members. Must be done by
        a team lead or a member with administrative permissions.
        """

        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_control_team(interaction.user, team):
            raise errors.ClearanceError(
                content="You do not have proper clearance to use this command"
            )

        member = interaction.guild.get_member(user.id)
        if member is None:
            member = await interaction.guild.fetch_member(user.id)

        if action == MemberAction.add:
            await team.add_member(member)

            await member.add_roles(
                discord.Object(team.member_roleid), reason="add to team"
            )

            await interaction.response.send_message(
                f"{member.mention} added to {team.name}",
                allowed_mentions=discord.AllowedMentions.none(),
                ephemeral=True,
            )
            return

        elif action == MemberAction.remove:
            await team.remove_member(user)

            if member is not None:
                await member.remove_roles(
                    discord.Object(team.member_roleid),
                    reason="remove from team",
                )

            await interaction.response.send_message(
                f"{user.mention} removed from {team.name}",
                allowed_mentions=discord.AllowedMentions.none(),
                ephemeral=True,
            )
            return

        elif action == MemberAction.edit:
            await interaction.response.send_message(
                f"Select up to 10 members to add to the team {team.name}",
                ephemeral=True,
                view=TeamUserEditView(team),
            )
            return

    @team.command(name="list")
    async def _list(self, interaction: Interaction):
        """
        Lists all the teams and short info of the guild
        """

        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_administrate_teams(interaction.user):
            raise errors.ClearanceError(
                content="You do not have proper clearance to use this command"
            )

        teams = await self.teams.force_fetch(interaction.guild)

        embed = discord.Embed(title="Team List")
        for team in teams.values():
            embed.add_field(
                name=team.name, value=await team.define_info(), inline=True
            )

        await interaction.response.send_message(embed=embed)

    @team.command(name="info")
    @app_commands.describe(team="The name of the team")
    async def _info(
        self,
        interaction: Interaction,
        team: app_commands.Transform[Team, TeamTransformer],
    ):
        """
        Provides info about the given team.
        """

        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_control_team(interaction.user, team):
            raise errors.ClearanceError(
                content="You do not have proper clearance to use this command"
            )

        await interaction.response.send_message(
            embed=await self.team_info(team), ephemeral=True
        )

    @team.command(name="memberlist")
    async def _memberlist(
        self,
        interaction: Interaction,
        team: app_commands.Transform[Team, TeamTransformer],
    ):
        """
        Provides a list of members that belong to the team
        """
        
        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_control_team(interaction.user, team):
            raise errors.ClearanceError(
                content="You do not have proper clearance to use this command"
            )

        members = [f"<@{m}>" for m in await team.fetch_members()]

        result = ", ".join(members)

        if result is None or result == "":
            result = "No members in the team"

        await interaction.response.send_message(result, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Main(bot))
