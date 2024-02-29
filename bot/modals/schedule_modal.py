import discord
from discord import Color, Embed, TextStyle
from discord import ui as dui

from bot import errors
from bot.constants import Channels
from bot.modals.text_inputs import DateInput
from bot.utils.types import Interaction


class ScheduleModal(dui.Modal, title="Schedule Request"):
    """A modal to send for schedule requests."""

    start_time: DateInput = DateInput(label="Start Time")
    end_time: DateInput = DateInput(label="End Time")

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

    pcs_needed: dui.TextInput = dui.TextInput(
        label="3) Number of PCs needed:",
        style=TextStyle.short,
        placeholder="0",
    )

    async def fetch_submission_channel(
        self, interaction: Interaction
    ) -> discord.abc.Messageable:
        """Fetch the channel to send the embed result to."""
        requestor_channel = Channels.schedule_requests

        if (guild := interaction.guild) is None:
            raise errors.InvalidInvocationError

        channel = await guild.fetch_channel(requestor_channel)
        if not isinstance(channel, discord.abc.Messageable):
            raise errors.InvalidInvocationError

        return channel

    async def on_submit(self, interaction: Interaction) -> None:  # type: ignore[override]
        """Send an embed to a channel that enables voting."""
        embed = Embed(
            title="Room Schedule Request",
            color=Color.from_str("#ffee00"),
            description=f"```\n{self.reason.value}\n```",
        )

        start_time = self.start_time.value
        end_time = self.end_time.value
        reoccuring = self.reoccuring.value
        pcs_needed = self.pcs_needed.value

        embed.add_field(name="Start at", value=start_time, inline=True)
        embed.add_field(name="Finish at", value=end_time, inline=True)
        embed.add_field(name="Reoccurs", value=reoccuring, inline=True)
        embed.add_field(name="PCs Needed", value=pcs_needed, inline=True)

        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar,
        )

        channel = await self.fetch_submission_channel(interaction)

        message = await channel.send(embed=embed)
        await message.create_thread(
            name=self.reason.value, auto_archive_duration=10_080
        )

        await interaction.response.send_message(
            "Time Requested", ephemeral=True
        )
