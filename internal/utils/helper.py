"""
Misc functions used in other multiple other parts of the bot's code
"""

from discord.ext import commands
import discord


def is_bot_admin(user: discord.User | discord.Member):
    """
    Checks if the user is a bot admin
    """

    return (
        user.id == 229779964898181120
    )  # currently strictly checks if it is me


async def get_or_fetch_channel(bot: commands.Bot, channel_id):
    channel = bot.get_channel(channel_id)

    if channel is None:
        channel = await bot.fetch_channel(channel_id)

    return channel


async def get_or_fetch_message(channel, message_id):
    try:
        return await channel.fetch_message(message_id)
    except:
        return None
