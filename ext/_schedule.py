
import enum
from discord import app_commands, Interaction
import discord

class RoomEvent:

    """
    represents a scheduled room event and whether its approved or not
    
    {
        id: int,

        title: str,
        start: str (timedelta-utc)
        end: str (timedelta-utc)

        author_id: int,
        is_approved: bool
    }
    """

class Occurance(enum.Enum):
    REOCCURING = 0
    INDIVIDUAL = 1

class ScheduleTimeForm(discord.ui.Modal, title="Schedule Time Form"):

    def __init__(self):
        self.event_title = discord.ui.TextInput()
        
        self.occurance = discord.ui.Select(
            placeholder="Occurance",

            # options=[enum_to_select(Occurance)]
        )

        self.date = discord.ui.Select(
            placeholder="Date(s) (can select up to 5)",
            min_values=1,
            max_values=5,

            options=[]
        ) # show the next 25 days

        self.start_time = discord.ui.Select(
            placeholder="Start Time",
            
        ) # show hours from 6am to 11PM

        self.end_time = discord.ui.Select(
            placeholder="End Time",

        ) # show hours from 7am to 12am

    async def on_submit(self, interaction: Interaction):
        pass

    async def interaction_check(self, interaction: Interaction):

        return True

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

        # send form
        # wait for form response
        # send message to logs to allow for approval

        # approval is a view with approve or deny buttons
        # once approved the event is added to the schedule

        pass

    @app_commands.command(name="edit")
    async def _edit(self, interaction: Interaction, id: int):
        """
        Allows exec members to edit a slot in the schedule, sends a modal
        similar to the request modal.
        
        """

        # extracts the data from the databse to fill the form with defaults
        # await response, check for any changes
        # update the database and calendar event
        
        pass

    @app_commands.command(name="remove")
    async def _remove(self, interaction: Interaction, id: int):
        """
        Allows exec members to remove a slot in the schedule or the requester
        to remove their approved time slot
        """

        # remove data from database and calendar

async def setup(bot):
    bot.tree.add_command(Main(bot))