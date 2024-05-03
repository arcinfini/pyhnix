from unittest.mock import AsyncMock, MagicMock

import discord
import discord.http
import pytest
import tests.mock as mock

from bot.client import Phoenix
from bot.utils.helper import (
    get_or_fetch_channel,
    get_or_fetch_message,
    is_bot_admin,
)


def test_is_bot_admin() -> None:
    """Test the is_bot_admin helper function."""
    # Mock User that should pass
    user = mock.User()
    user.id = 229779964898181120
    assert is_bot_admin(user) is True

    # Mock user that should fail
    user = mock.User()
    user.id = 123456789012345678
    assert is_bot_admin(user) is False


@pytest.mark.asyncio
async def test_get_or_fetch_channel(
    not_found: discord.NotFound, forbidden: discord.Forbidden
) -> None:
    """Test the get_or_fetch_channel helper function."""
    mock_bot = AsyncMock(spec=Phoenix)
    channel_id = 123456789012345678

    # Scenario 1: Channel is found in cache
    expected_channel = MagicMock()
    mock_bot.get_channel.return_value = expected_channel
    channel = await get_or_fetch_channel(mock_bot, channel_id)
    assert channel is expected_channel
    mock_bot.get_channel.assert_called_once_with(channel_id)
    mock_bot.fetch_channel.assert_not_called()

    # Scenario 2: Channel not found in cache, needs to be fetched
    mock_bot.get_channel.return_value = None
    mock_bot.fetch_channel.return_value = expected_channel
    channel = await get_or_fetch_channel(mock_bot, channel_id)
    assert channel is expected_channel
    mock_bot.fetch_channel.assert_called_once_with(channel_id)

    # Scenario 3: Channel is not found in cache, fetch channel fails with NotFound
    mock_bot.get_channel.return_value = None
    mock_bot.fetch_channel.side_effect = not_found
    channel = await get_or_fetch_channel(mock_bot, channel_id)
    assert channel is None

    # Scenario 4: Channel not in cache and cannot be fetched with Forbidden
    mock_bot.get_channel.return_value = None
    mock_bot.fetch_channel.side_effect = forbidden
    channel = await get_or_fetch_channel(mock_bot, channel_id)
    assert channel is None


@pytest.mark.asyncio
async def test_get_or_fetch_message(
    not_found: discord.NotFound, forbidden: discord.Forbidden
) -> None:
    """Test the get_or_fetch_message helper function."""
    mock_channel = AsyncMock(spec=discord.PartialMessageable)
    message_id = 123456789012345678

    # Scenario 1: Message is successfully fetched
    expected_message = MagicMock(spec=discord.Message)
    mock_channel.fetch_message.return_value = expected_message
    message = await get_or_fetch_message(mock_channel, message_id)
    assert message is expected_message

    # Scenario 2: Message fetch fails with NotFound error
    mock_channel.fetch_message.side_effect = not_found
    message = await get_or_fetch_message(mock_channel, message_id)
    assert message is None

    # Scenario 3: Message fetch fails with Forbidden error
    mock_channel.fetch_message.side_effect = forbidden
    message = await get_or_fetch_message(mock_channel, message_id)
    assert message is None
