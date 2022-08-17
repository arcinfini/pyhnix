import traceback
from discord import app_commands, Interaction

class PhoenixTree(app_commands.CommandTree):
    """"""

    async def on_error(self, interaction: Interaction, error):
        # check error
        # input error
        # environment error

        # if not caught, send error to discord logs

        await super().on_error(interaction, error)