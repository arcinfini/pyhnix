import discord
from discord.interactions import Interaction


class GuildInteraction(Interaction):
    guild: discord.Guild
