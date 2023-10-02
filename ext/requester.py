from re import compile as recompile
from internal.client import Phoenix
from discord.ext import commands
from discord import app_commands, Interaction, ui as dui, TextStyle
import discord

from internal import errors



class ScheduleModal(dui.Modal, title="Schedule Request"):
    start_time = dui.TextInput(
        label="Start Time",
        style=TextStyle.short,
        placeholder="DOTW MM-DD(-YY) HH:MM AM/PM",
        default="Tuesday 12-01 10:00 PM",
    )
    end_time = dui.TextInput(
        label="End Time",
        style=TextStyle.short,
        placeholder="(MM-DD-YY) HH:MM AM/PM",
        default="11:00 PM",
    )
    reason = dui.TextInput(
        label="1) What is this form being filled out for:",
        style=TextStyle.paragraph,
        placeholder="Ex: Overwatch Practice / Overwatch Away Game",
    )
    reoccuring = dui.TextInput(
        label="2) Is this reoccurring weekly:",
        style=TextStyle.short,
        placeholder="Yes or No",
    )

    async def on_submit(self, interaction: Interaction[Phoenix]) -> None:
        """
        Send an embed to a channel that enables voting
        """

        embed = discord.Embed(
            title="Room Schedule Request",
            color=discord.Color.from_str("#00ff37"),
        )

        embed.add_field(name="Start", value=self.start_time.value, inline=True)
        embed.add_field(name="End", value=self.end_time.value, inline=True)
        embed.add_field(
            name="Reoccurs", value=self.reoccuring.value, inline=True
        )

        embed.add_field(
            name="Information",
            value=f"```\n{self.reason.value}\n```",
            inline=False,
        )

        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar,
        )
        embed.set_footer(text="0/3")

        requestor_channel = interaction.client.config["ids"]["channels"][
            "schedule-requests"
        ]

        if (guild := interaction.guild) is None:
            raise errors.InvalidInvocationError()

        channel = await guild.fetch_channel(requestor_channel)
        if not isinstance(channel, discord.TextChannel):
            raise errors.InvalidInvocationError()

        await channel.send(embed=embed)

        await interaction.response.send_message(
            "Time Requested", ephemeral=True
        )


class Main(commands.Cog, name="Schedule"):
    def __init__(self, bot):
        self.bot: Phoenix = bot

    request = app_commands.Group(
        name="request",
        description="different subcommands allow for the request of different \
            things",
    )

    @request.command(name="schedule")
    async def _schedule(self, interaction: Interaction):
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


async def setup(bot):
    await bot.add_cog(Main(bot))
