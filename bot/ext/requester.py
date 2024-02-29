from discord import Interaction, app_commands

from bot.client import Phoenix
from bot.gear import Gear
from bot.modals.schedule_modal import ScheduleModal


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
