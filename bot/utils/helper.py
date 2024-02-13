from typing import Optional, TYPE_CHECKING, Union

import discord
from discord import Message, PartialMessageable
from discord.ext import commands

if TYPE_CHECKING:
    from discord import Thread
    from discord.abc import GuildChannel, PrivateChannel

    Channel = Union[GuildChannel, PrivateChannel, Thread]


def is_bot_admin(user: discord.User | discord.Member) -> bool:
    """Check if the user is a bot admin."""
    return (
        user.id == 229779964898181120
    )  # currently strictly checks if it is me


async def get_or_fetch_channel(
    bot: commands.Bot, channel_id: int
) -> Optional["Channel"]:
    """Search for the channel in the cache, otherwise fetch."""
    channel = bot.get_channel(channel_id)

    if channel is None:
        channel = await bot.fetch_channel(channel_id)

    return channel


async def get_or_fetch_message(
    channel: PartialMessageable, message_id: int
) -> Optional[Message]:
    """Search for the message in the cache, otherwise fetch."""
    try:
        return await channel.fetch_message(message_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None
