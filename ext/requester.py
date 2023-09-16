from re import compile as recompile
from internal.client import Phoenix
from discord.ext import commands
from discord import (
    app_commands,
    Interaction,
    ui as dui,
    TextStyle
)
import discord

class ApprovalView(dui.View):

    def __init__(self, approval_id, deny_id):
        super().__init__(timeout=None)

        self._approve.custom_id = approval_id
        self._deny.custom_id = deny_id

        self.compiled = recompile(r"-?\d+/\d+")

    async def interaction_check(self, interaction: Interaction[Phoenix]) -> bool:
        result = 484489190801801218 in [r.id for r in interaction.user.roles]

        if not result:
            await interaction.response.send_message("You can't do that", ephemeral=True)

        return result

    @dui.button(label="Approve", style=discord.ButtonStyle.green)
    async def _approve(self, interaction:Interaction, button: dui.Button):
        """
        Votes for the approval of the schedule change
        """

        embed = interaction.message.embeds[0]
        vote = self.compiled.match(embed.footer.text)

        if not vote: return

        current, required = [int(i) for i in vote.group(0).split("/")]

        current += 1

        embed.set_footer(text=f"{current}/{required}")

        await interaction.response.edit_message(embed=embed)


    @dui.button(label="Deny", style=discord.ButtonStyle.red)
    async def _deny(self, interaction:Interaction, button:dui.Button):
        """
        Votes for the denial of the schedule change
        """

        embed = interaction.message.embeds[0]
        vote = self.compiled.match(embed.footer.text)

        if not vote: return

        current, required = [int(i) for i in vote.group(0).split("/")]

        current += -1

        embed.set_footer(text=f"{current}/{required}")

        await interaction.response.edit_message(embed=embed)

class ScheduleModal(dui.Modal, title="Schedule Request"):
    start_time = dui.TextInput(
        label="Start Time", 
        style=TextStyle.short, 
        placeholder="DOTW MM-DD(-YY) HH:MM AM/PM",
        default="Tuesday 12-01 10:00 PM"
    )
    end_time = dui.TextInput(
        label="End Time",
        style=TextStyle.short,
        placeholder="(MM-DD-YY) HH:MM AM/PM",
        default="11:00 PM"
    )
    reason = dui.TextInput(
        label="1) What is this form being filled out for:",
        style=TextStyle.paragraph,
        placeholder="Ex: Overwatch Practice / Overwatch Away Game"
    )
    reoccuring = dui.TextInput(
        label="2) Is this reoccurring weekly:",
        style=TextStyle.short,
        placeholder="Yes or No"
    )

    def __init__(self, view) -> None:
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: Interaction[Phoenix]) -> None:
        """
        Send an embed to a channel that enables voting
        """

        embed = discord.Embed(
            title="Room Schedule Request",
            color=discord.Color.from_str("#00ff37")
        )

        embed.add_field(name="Start", value=self.start_time.value, inline=True)
        embed.add_field(name="End", value=self.end_time.value, inline=True)
        embed.add_field(name="Reoccurs", value=self.reoccuring.value, inline=True)

        embed.add_field(
            name="Information", 
            value=f"```\n{self.reason.value}\n```", 
            inline=False
        )

        embed.set_author(
            name=interaction.user.display_name, 
            icon_url=interaction.user.display_avatar
        )
        embed.set_footer(text="0/3")

        channel = await interaction.guild.fetch_channel(1152411129465819207)
        await channel.send(embed=embed, view=self.view)

        await interaction.response.send_message("Time Requested", ephemeral=True)
    

    

class Main(commands.Cog, name="Schedule"):

    def __init__(self, bot):
        self.bot: Phoenix = bot

    async def cog_load(self):
        self.APPROVAL_VIEW=ApprovalView(
            approval_id = f"APPROVE-{self.bot.user.id}",
            deny_id = f"DENY-{self.bot.user.id}"
        )

        self.bot.add_view(self.APPROVAL_VIEW)

    async def cog_unload(self) -> None:
        
        self.APPROVAL_VIEW.stop()

    request = app_commands.Group(
        name="request", 
        description="different subcommands allow for the request of different things"
    )

    @request.command(name="schedule")
    async def _schedule(self, interaction: Interaction):
        modal = ScheduleModal(view=self.APPROVAL_VIEW)
        
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