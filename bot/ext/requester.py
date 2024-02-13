import discord
from discord import Interaction, TextStyle, app_commands
from discord import ui as dui

from bot import constants, errors
from bot.client import Phoenix
from bot.gear import Gear


class ScheduleModal(dui.Modal, title="Schedule Request"):
    """A modal to send for schedule requests."""

    start_time: dui.TextInput = dui.TextInput(
        label="Start Time",
        style=TextStyle.short,
        placeholder="DOTW MM-DD(-YY) HH:MM AM/PM",
        default="Tuesday 12-01 10:00 PM",
    )
    end_time: dui.TextInput = dui.TextInput(
        label="End Time",
        style=TextStyle.short,
        placeholder="(MM-DD-YY) HH:MM AM/PM",
        default="11:00 PM",
    )
    reason: dui.TextInput = dui.TextInput(
        label="1) What is this form being filled out for:",
        style=TextStyle.paragraph,
        placeholder="Ex: Overwatch Practice / Overwatch Away Game",
    )
    reoccuring: dui.TextInput = dui.TextInput(
        label="2) Is this reoccurring weekly:",
        style=TextStyle.short,
        placeholder="Yes or No",
    )

    async def on_submit(self, interaction: Interaction[Phoenix]) -> None:  # type: ignore[override]
        """Send an embed to a channel that enables voting."""
        embed = discord.Embed(
            title="Room Schedule Request",
            color=discord.Color.from_str("#ffee00"),
            description=f"```\n{self.reason.value}\n```",
        )

        embed.add_field(
            name="Start at", value=self.start_time.value, inline=True
        )
        embed.add_field(
            name="Finish at", value=self.end_time.value, inline=True
        )
        embed.add_field(
            name="Reoccurs", value=self.reoccuring.value, inline=False
        )

        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar,
        )

        requestor_channel = constants.Channels.schedule_requests

        if (guild := interaction.guild) is None:
            raise errors.InvalidInvocationError

        channel = await guild.fetch_channel(requestor_channel)
        if not isinstance(channel, discord.abc.Messageable):
            raise errors.InvalidInvocationError

        await channel.send(embed=embed)

        await interaction.response.send_message(
            "Time Requested", ephemeral=True
        )


class Main(Gear, name="Schedule"):
    """Requests within the discord."""

    request = app_commands.Group(
        name="request",
        description="different subcommands allow for the request of different \
            things",
    )

    @request.command(name="schedule")
    async def _schedule(self, interaction: Interaction) -> None:
        """Request a schedule change."""
        modal = ScheduleModal()

        await interaction.response.send_modal(modal)

    # @request.command(name="travel")
    # async def _travel(self, interaction: Interaction):
    #     await interaction.response.send_modal(TravelModal())

    # class TravelModal(RequestModal, title="Travel Request"):
    # address = dui.TextInput(
    #     label="Address of location:",
    #     style=TextStyle.short,
    #     placeholder="Ex: 100 Campus Dr, Elon, NC 27244"
    # )
    # overnight = dui.TextInput(
    #     label="Does this require an overnight stay?",
    #     style=TextStyle.short,
    #     placeholder="EX: Yes, we need to accomadate for 7 people"
    # )


async def setup(bot: Phoenix) -> None:
    """Load the requester module."""
    await bot.add_cog(Main(bot))
