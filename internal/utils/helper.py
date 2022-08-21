
from discord.ext import commands
import discord

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