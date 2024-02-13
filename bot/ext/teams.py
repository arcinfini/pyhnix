import logging
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

_log = logging.getLogger(__name__)


class TeamUserEditView(dui.View):
    """A view provided when editing multiple users in a team."""

    def __init__(self, team: Team):
        super().__init__()
        self.team = team

    @dui.select(cls=dui.UserSelect, min_values=0, max_values=10)
    async def _user_select(
        self, interaction: "Interaction", select: dui.UserSelect
    ) -> None:
        """Defer the interaction with thinking False.

        This allows the interaction to proceed.
        """
        await interaction.response.defer(thinking=False)

    @dui.button(label="Add to team")
    async def _add_team(
        self, interaction: "Interaction", button: dui.Button
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
        self, interaction: "Interaction", button: dui.Button
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

    team = app_commands.Group(
        name="team",
        description="Team commands",
        guild_only=True,
    )

    members = app_commands.Group(
        name="members",
        description="Use this to control members",
        guild_only=True,
    )
    team.add_command(members)

    manage = app_commands.Group(
        name="manage",
        description="Use this to control team configurations",
        guild_only=True,
    )
    team.add_command(manage)

    def __init__(self, client: Phoenix) -> None:
        self.client = client

    async def team_info(self, team: Team) -> discord.Embed:
        """Create a simple embed of team info to return."""
        return discord.Embed(
            title="Team Info", description=await team.define_info()
        )

    async def interaction_check(self, interaction: "Interaction") -> bool:  # type: ignore[override]
        """Check if the interaction should be ran.

        This check makes sure the command is ran in a guild.

        If a team parameter is defined within the command, the check should
        determine if the user can manage the team. This is true if the member is
        and administrator or if the member has the team lead role.
        """
        member = interaction.user
        if not isinstance(member, discord.Member):
            raise errors.InvalidInvocationError(
                content="This command can only be ran in a server."
            )

        if member.guild_permissions.administrator:
            return True

        command = interaction.command
        if command is None:
            return True

        # if the user was an administrator it would have returned true
        # already. therefore this should return false if it is a manage
        # command.
        if (
            not isinstance(command, app_commands.ContextMenu)
            and (parent := command.parent) is not None
            and parent == self.manage
        ):
            return False

        # Check if team is present in parameters.
        # If it is not in the parameters list then return True as no checks need
        # to be carried out.
        team_name = interaction.namespace.team
        if team_name is None or not isinstance(team_name, str):
            _log.debug(
                "no string team parameter found in %s", command.qualified_name
            )

            return True

        # Check if interaction invoker has the team lead role
        team = await TeamTransformer().transform(interaction, team_name)

        return team.lead_role_id in [r.id for r in member.roles]

    @team.command(name="info")
    async def _team_info_info(
        self,
        interaction: "Interaction",
        team: app_commands.Transform[Team, TeamTransformer],
    ) -> None:
        """Return information about a team."""
        await interaction.response.send_message(
            embed=await self.team_info(team), ephemeral=True
        )

    @team.command(name="list")
    async def _team_info_list(self, interaction: "Interaction") -> None:
        """Return information about all teams."""
        guild = interaction.guild
        if guild is None:
            raise errors.InvalidInvocationError(
                content="This command can only be ran in a server."
            )

        teams = await self.client.get_team_guild(guild).fetch_teams()

        embed = discord.Embed(title="Team List")
        for team in teams:
            embed.add_field(
                name=team.name, value=await team.define_info(), inline=True
            )

        await interaction.response.send_message(embed=embed)

    @team.command(name="memberlist")
    async def _team_info_members(
        self,
        interaction: "Interaction",
        team: app_commands.Transform[Team, TeamTransformer],
    ) -> None:
        """Return a list of members within the team."""
        members = [f"<@{m}>" for m in await team.fetch_members()]

        result = ", ".join(members)

        if result is None or result == "":
            result = "No members in the team"

        await interaction.response.send_message(result, ephemeral=True)

    @members.command(name="add")
    async def _team_members_add(
        self,
        interaction: "Interaction",
        team: app_commands.Transform[Team, TeamTransformer],
        member: discord.Member,
    ) -> None:
        """Add a member to a team."""
        await team.add_member(member)

        await member.add_roles(
            discord.Object(team.member_role_id), reason="add to team"
        )

        await interaction.response.send_message(
            f"{member.mention} added to {team.name}",
            allowed_mentions=discord.AllowedMentions.none(),
            ephemeral=True,
        )

    @members.command(name="remove")
    async def _team_members_remove(
        self,
        interaction: "Interaction",
        team: app_commands.Transform[Team, TeamTransformer],
        user: discord.User,
    ) -> None:
        """Remove a member from a team."""
        await team.remove_member(user)

        guild = interaction.guild
        if (
            guild is not None
            and (member := await guild.fetch_member(user.id)) is not None
        ):
            await member.remove_roles(
                discord.Object(team.member_role_id),
                reason="remove from team",
            )

        await interaction.response.send_message(
            f"{user.mention} removed from {team.name}",
            allowed_mentions=discord.AllowedMentions.none(),
            ephemeral=True,
        )
        return

    @members.command(name="edit")
    async def _team_members_edit(
        self,
        interaction: "Interaction",
        team: app_commands.Transform[Team, TeamTransformer],
    ) -> None:
        """Edit members on a team."""
        await interaction.response.send_message(
            f"Select up to 10 members to add to the team {team.name}",
            ephemeral=True,
            view=TeamUserEditView(team),
        )

    @members.command(name="clean")
    async def _team_members_clean(
        self,
        interaction: "Interaction",
        team: app_commands.Transform[Team, TeamTransformer],
    ) -> None:
        """Clear all the members from a team."""
        guild = interaction.guild
        if guild is None:
            raise errors.InvalidInvocationError(
                content="This command can only be ran in a server."
            )

        failed = []

        await interaction.response.defer(ephemeral=True)

        mem_ids = await team.fetch_members()
        for member_id in mem_ids:
            try:
                await team.remove_member(discord.Object(member_id))

                member = await guild.fetch_member(member_id)
                await member.remove_roles(discord.Object(team.member_role_id))
            except Exception:
                failed.append(member_id)

        failed_for = [f"<@{id}>" for id in failed]
        await interaction.edit_original_response(
            content=f"Completed interaction\nFailed for {failed_for}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @manage.command(name="create")
    async def _team_manage_create(
        self,
        interaction: "Interaction",
        name: str,
        lead: discord.Role,
        role: discord.Role,
    ) -> None:
        """Create a team in the guild with the provided properties."""
        guild = interaction.guild
        if guild is None:
            raise errors.InvalidInvocationError(
                content="This command can only be ran in a server."
            )

        try:
            team = await self.client.get_team_guild(guild).create_team(
                name=name, lead_role=lead, member_role=role
            )

            await interaction.response.send_message(f"{team.name} was created")
        except asyncpg.UniqueViolationError:
            await interaction.response.send_message(
                f"A team with name `{name}` already exists in this server"
            )

    @manage.command(name="edit")
    async def _team_manage_edit(
        self,
        interaction: "Interaction",
        team: app_commands.Transform[Team, TeamTransformer],
        name: str | None,
        lead: discord.Role | None,
        role: discord.Role | None,
    ) -> None:
        """Edit the provided properties of a provided team."""
        await interaction.response.defer()

        await team.edit(name=name, lead_role=lead, member_role=role)
        # TODO: update member roles to new role

        await interaction.followup.send(
            f"{team.name} updated | new team info",
            embed=await self.team_info(team),
        )

    @manage.command(name="delete")
    async def _team_manage_delete(
        self,
        interaction: "Interaction",
        team: app_commands.Transform[Team, TeamTransformer],
    ) -> None:
        """Delete a team."""
        # TODO: clean the team members
        await team.delete()

        await interaction.response.send_message(
            "%s was deleted" % team.name,
        )


async def setup(bot: Phoenix) -> None:
    """Load the teams module."""
    await bot.add_cog(Main(bot))
