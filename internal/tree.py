import traceback
from discord import app_commands, Interaction

class PhoenixTree(app_commands.CommandTree):
    """"""

    async def on_error(self, interaction: Interaction, error):
        print(traceback.format_exc())