
from discord import app_commands, Interaction

class Main(app_commands.Group):

    def __init__(self, bot):
        super().__init__(name="schedule")

        self.bot = bot

    @app_commands.command(name="request")
    async def _request(self, interaction: Interaction):
        """
        Allows a team lead to request a slot in the schedule, sends a modal
        
        type: reoccuring or single event
        date: mm-dd-yy format
        start: HH:MM AM/PM
        end: HH:MM AM/PM
        title:
        """

        pass

    @app_commands.command(name="edit")
    async def _edit(self, interaction: Interaction, id: int):
        """
        Allows exec members to edit a slot in the schedule, sends a modal
        similar to the request modal.
        
        """
        
        pass

    @app_commands.command(name="remove")
    async def _remove(self, interaction: Interaction, id: int):
        """
        Allows exec members to remove a slot in the schedule or the requester
        to remove their approved time slot
        """

async def setup(bot):
    bot.tree.add_command(Main(bot))