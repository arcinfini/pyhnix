
from discord import app_commands, Interaction

from .utils import checks

async def is_bot_admin():
    def predicate(interaction: Interaction):
        return checks.is_bot_admin(interaction.user)
    return app_commands.check(predicate)