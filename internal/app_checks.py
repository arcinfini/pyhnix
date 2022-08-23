
from discord import app_commands, Interaction

from .utils import helper

def is_bot_admin():
    def predicate(interaction: Interaction):
        return helper.is_bot_admin(interaction.user)
    return app_commands.check(predicate)