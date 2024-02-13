import discord
from discord.interactions import Interaction
from internal.client import Phoenix


class GuildInteraction(Interaction):
    guild: discord.Guild
    user: discord.Member
    client: Phoenix
