import enum
import logging
import typing
from typing import TYPE_CHECKING

import asyncpg
import discord
import discord.ui as dui
from discord import app_commands
from discord.ext import commands
from discord.utils import get

from bot import errors
from bot.client import Phoenix
from bot.team import Team

if TYPE_CHECKING:
    from bot.utils.types import Interaction

logger = logging.getLogger(__name__)


class MemberAction(enum.Enum):
    """An enum that determines an action taken on a command."""

    add = 0
    remove = 1
    edit = 2


class TeamUserEditView(dui.View):
    """A view provided when editing multiple users in a team."""

    def __init__(self, team: Team):
        super().__init__()
        self.team = team

    @dui.select(cls=dui.UserSelect, min_values=0, max_values=10)
    async def _user_select(
        self, interaction: Interaction, select: dui.UserSelect
    ) -> None:
        """Defer the interaction with thinking False.

        This allows the interaction to proceed.
        """
        await interaction.response.defer(thinking=False)

    @dui.button(label="Add to team")
    async def _add_team(
        self, interaction: Interaction, button: dui.Button
    ) -> None:
        """Add the selected member(s) to a team."""
        await interaction.response.defer(ephemeral=True)

        for member in self._user_select.values:
            if not isinstance(member, discord.Member):
                raise errors.InvalidInvocationError(
                    content="This command is returning a user rather than a \
                        server member"
                )

            if member.get_role(self.team.member_role_id) is not None:
                continue

            await self.team.add_member(member)
            await member.add_roles(
                discord.Object(self.team.member_role_id), reason="add to team"
            )

        await interaction.followup.send("Members edited", ephemeral=True)

    @dui.button(label="Remove from Team")
    async def _remove_team(
        self, interaction: Interaction, button: dui.Button
    ) -> None:
        """Remove the selected member(s) from a team."""
        await interaction.response.defer(ephemeral=True)

        for member in self._user_select.values:
            if not isinstance(member, discord.Member):
                raise errors.InvalidInvocationError(
                    content="This command is returning a user rather than a \
                        server member"
                )

            if member.get_role(self.team.member_role_id) is None:
                continue

            await self.team.remove_member(member)
            await member.remove_roles(
                discord.Object(self.team.member_role_id),
                reason="remove from team",
            )

        await interaction.followup.send("Members edited", ephemeral=True)


class TeamTransformer(app_commands.Transformer):
    """A transformer for Teams."""

    async def transform(self, interaction: "Interaction", value: str) -> Team:
        """Transform the value into a team."""
        if interaction.guild is None:
            raise errors.InvalidInvocationError

        client = interaction.client
        team_guild = client.get_team_guild(interaction.guild)

        teams = await team_guild.fetch_teams()
        team = get(teams, name=value)

        if team is None:
            raise errors.TransformationError(
                content="Team with name '%s' not found." % value
            )

        return team

    async def autocomplete(  # type: ignore[override]
        self,
        interaction: "Interaction",
        value: str,  # type: ignore[override]
    ) -> list[app_commands.Choice[str]]:
        """Return a list of valid choices for the user to pick."""
        if interaction.guild is None:
            raise errors.InvalidInvocationError

        client = interaction.client
        team_guild = client.get_team_guild(interaction.guild)

        teams = await team_guild.fetch_teams()

        def contains(x: Team) -> bool:
            return value in x.name

        def make_choice(x: Team) -> app_commands.Choice[str]:
            return app_commands.Choice(name=x.name, value=x.name)

        return [make_choice(value) for value in filter(contains, teams)]


@app_commands.default_permissions(manage_roles=True)
class Main(commands.Cog, name="Teams"):
    """A module containing functionality for teams."""

    def __init__(self, client: Phoenix) -> None:
        self.client = client

    async def team_info(self, team: Team) -> discord.Embed:
        """Create a simple embed of team info to return."""
        return discord.Embed(
            title="Team Info", description=await team.define_info()
        )

    def can_administrate_teams(self, member: discord.Member) -> bool:
        """Check if the member can administrate teams."""
        return member.guild_permissions.administrator

    def can_control_team(self, member: discord.Member, team: Team) -> bool:
        """Check if the member can control teams."""
        return team.lead_role_id in [
            r.id for r in member.roles
        ] or self.can_administrate_teams(member)

        if member is None:
            return False

        return team.lead_roleid in [
            r.id for r in member.roles
        ] or self.can_administrate_teams(member)

    async def interaction_check(self, interaction: "Interaction") -> bool:  # type: ignore[override]
        """Pass this check through the module.

        Member needs to have manage role permissions or administrator
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
        interaction: "Interaction",
        team: app_commands.Transform[Team, TeamTransformer],
    ) -> None:
        """Retreive all the members of a team and remove them from it."""
        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_administrate_teams(interaction.user):
            raise errors.InvalidAuthorizationError(
                content="You do not have proper clearance to use this command"
            )

        failed = []

        await interaction.response.defer(ephemeral=True)

        mem_ids = await team.fetch_members()
        for member_id in mem_ids:
            try:
                await team.remove_member(discord.Object(member_id))

                member = await interaction.guild.fetch_member(member_id)
                await member.remove_roles(discord.Object(team.member_role_id))
            except Exception:
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
        interaction: "Interaction",
        name: str,
        lead: discord.Role,
        role: discord.Role,
    ) -> None:
        """Create a new team for the guild."""
        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_administrate_teams(interaction.user):
            raise errors.InvalidAuthorizationError(
                content="You do not have proper clearance to use this command"
            )

        try:
            guild_team = interaction.client.get_team_guild(interaction.guild)
            team = await guild_team.create_team(
                name=name, lead_role=lead, member_role=role
            )

            await interaction.response.send_message(f"{team.name} was created")
        except asyncpg.UniqueViolationError:
            await interaction.response.send_message(
                f"A team with name `{name}` already exists in this server"
            )

    @team.command(name="delete")
    @app_commands.describe(team="The name of the team")
    async def _delete(
        self,
        interaction: "Interaction",
        team: app_commands.Transform[Team, TeamTransformer],
    ) -> None:
        """Delete a team from the guild.

        Asks for clarification. Can only be done by server administrators
        """
        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_administrate_teams(interaction.user):
            raise errors.InvalidAuthorizationError(
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
        interaction: "Interaction",
        team: app_commands.Transform[Team, TeamTransformer],
        lead: typing.Optional[discord.Role],
        role: typing.Optional[discord.Role],
        name: typing.Optional[str],
    ) -> None:
        """Edit a team's properties.

        Can only be done by server administrators,
        """
        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_administrate_teams(interaction.user):
            raise errors.InvalidAuthorizationError(
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
        interaction: "Interaction",
        action: MemberAction,
        user: discord.User,
        team: app_commands.Transform[Team, TeamTransformer],
    ) -> None:
        """Add or remove a member from the list of team members.

        Must be done by a team lead or a member with administrative permissions.
        """
        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_control_team(interaction.user, team):
            raise errors.InvalidAuthorizationError(
                content="You do not have proper clearance to use this command"
            )

        member = interaction.guild.get_member(user.id)
        if member is None:
            member = await interaction.guild.fetch_member(user.id)

        if action == MemberAction.add:
            await team.add_member(member)

            await member.add_roles(
                discord.Object(team.member_role_id), reason="add to team"
            )

            await interaction.response.send_message(
                f"{member.mention} added to {team.name}",
                allowed_mentions=discord.AllowedMentions.none(),
                ephemeral=True,
            )

        elif action == MemberAction.remove:
            await team.remove_member(user)

            if member is not None:
                await member.remove_roles(
                    discord.Object(team.member_role_id),
                    reason="remove from team",
                )

            await interaction.response.send_message(
                f"{user.mention} removed from {team.name}",
                allowed_mentions=discord.AllowedMentions.none(),
                ephemeral=True,
            )

        elif action == MemberAction.edit:
            await interaction.response.send_message(
                f"Select up to 10 members to add to the team {team.name}",
                ephemeral=True,
                view=TeamUserEditView(team),
            )

    @team.command(name="list")
    async def _list(self, interaction: "Interaction") -> None:
        """List all the teams and short info of the guild."""
        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_administrate_teams(interaction.user):
            raise errors.InvalidAuthorizationError(
                content="You do not have proper clearance to use this command"
            )

        guild_team = interaction.client.get_team_guild(interaction.guild)
        teams = await guild_team.fetch_teams()

        embed = discord.Embed(title="Team List")
        for team in teams:
            embed.add_field(
                name=team.name, value=await team.define_info(), inline=True
            )

        await interaction.response.send_message(embed=embed)

    @team.command(name="info")
    @app_commands.describe(team="The name of the team")
    async def _info(
        self,
        interaction: "Interaction",
        team: app_commands.Transform[Team, TeamTransformer],
    ) -> None:
        """Send an embed with info about the team."""
        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_control_team(interaction.user, team):
            raise errors.InvalidAuthorizationError(
                content="You do not have proper clearance to use this command"
            )

        await interaction.response.send_message(
            embed=await self.team_info(team), ephemeral=True
        )

    @team.command(name="memberlist")
    async def _memberlist(
        self,
        interaction: "Interaction",
        team: app_commands.Transform[Team, TeamTransformer],
    ) -> None:
        """Provide a list of members that belong to the team."""
        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            raise errors.InvalidInvocationError(
                content="This command should be used within a guild"
            )

        if not self.can_control_team(interaction.user, team):
            raise errors.InvalidAuthorizationError(
                content="You do not have proper clearance to use this command"
            )

        members = [f"<@{m}>" for m in await team.fetch_members()]

        result = ", ".join(members)

        if result is None or result == "":
            result = "No members in the team"

        await interaction.response.send_message(result, ephemeral=True)


async def setup(bot: Phoenix) -> None:
    """Load the teams module."""
    await bot.add_cog(Main(bot))
