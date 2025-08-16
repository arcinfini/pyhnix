import discord
from discord import Interaction, app_commands

from bot.core import Client, Gear
from bot.model import teams


class Main(Gear, name="Teams"):
    """Team commands."""

    team = app_commands.Group(
        name="team",
        description="Team commands",
        guild_only=True,
    )

    team_members = app_commands.Group(
        name="members",
        description="Use this to control members",
        guild_only=True,
    )

    team_manage = app_commands.Group(
        name="manage",
        description="Use this to control team configurations",
        guild_only=True,
    )

    team.add_command(team_members)
    team.add_command(team_manage)

    @team.command(name="list")
    async def _team_list(self, interaction: Interaction) -> None:
        """Return a list of all teams."""
        await interaction.response.defer(ephemeral=True)

        team_list = await teams.fetch_teams(interaction.guild)
        embed = discord.Embed(title="Team List")

        for team in team_list:
            embed.add_field(name=team.name, value=f"```{team.describe()}```")

        if len(team_list) == 0:
            embed.description = "```Guild has no teams.```"

        await interaction.response.send(embed=embed)

    @team_members.command(name="list")
    async def _team_members_list(
        self, interaction: Interaction, team: str
    ) -> None:
        """Return the current memberlist of the team."""
        await interaction.response.defer(ephemeral=True)

        member_list = await team.fetch_members()
        member_list_text = " ".join([f"<@{m.id}>" for m in member_list])

        await interaction.response.send(
            f"{team.name} Member List:\n{member_list_text}"
        )

    @team_members.command(name="add")
    async def _team_members_add(
        self, interaction: Interaction, team: str, member: discord.Member
    ) -> None:
        """Add a member to a team."""
        await interaction.response.defer(ephemeral=True)

        member_role = await team.member_role.resolve()

        await team.add_member(member)
        await member.add_role(member_role)

        await interaction.response.send(
            f"Member successfully added to {team.name}"
        )

    @team_members.command(name="remove")
    async def _team_members_remove(
        self, interaction: Interaction, team: str, member: discord.Member
    ) -> None:
        """Remove a member from a team."""
        await interaction.response.defer(ephemeral=True)

        member_role = await team.member_role.resolve()

        await team.add_member(member)
        await member.remove_role(member_role)

        await interaction.response.send(
            f"Member successfully removed from {team.name}"
        )

    @team_members.command(name="edit")
    async def _team_members_edit(
        self, interaction: Interaction, team: str
    ) -> None:
        """Edit the list of members on a team."""

    @team_members.command(name="clean")
    async def _team_members_clean(
        self, interaction: Interaction, team: str
    ) -> None:
        """Clear the list of members for a team.

        This may take a few minutes.
        """

    @team_manage.command(name="create")
    @app_commands.describe(
        name="Provide the name for the new team.",
        lead="Select the role that will manage the new team.",
        role="Select the role that will be given to team members.",
    )
    async def _team_manage_create(
        self,
        interaction: Interaction,
        name: str,
        lead: discord.Role,
        role: discord.Role,
    ) -> None:
        """Create a new team in the guild with the provided details."""

    @team_manage.command(name="edit")
    @app_commands.describe(
        name="Provide a new name if desired." "",
        lead="Select an updated role that will manage the team.",
        role="Select an updated role that will be given to team members.",
    )
    async def _team_manage_edit(
        self,
        interaction: Interaction,
        team: str,
        name: str | None,
        lead: discord.Role | None,
        role: discord.Role | None,
    ) -> None:
        """Edit a team in the guild with the provided updated details.

        This may take a few minutes if you are updating the team member role.
        """

    @team_manage.command(name="delete")
    async def _team_manage_delete(
        self, interaction: Interaction, team: str
    ) -> None:
        """Delete a team."""


async def setup(bot: Client) -> None:
    """Initialize the module."""
    await bot.add_cog(Main(bot))
