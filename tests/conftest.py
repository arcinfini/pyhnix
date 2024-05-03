from unittest.mock import MagicMock

import discord
import pytest
from aiohttp.client import ClientResponse


@pytest.fixture
def not_found() -> discord.NotFound:
    class MockResponse(MagicMock):
        spec = ClientResponse

    return discord.NotFound(MockResponse(), "not found")


@pytest.fixture
def forbidden() -> discord.Forbidden:
    class MockResponse(MagicMock):
        spec = ClientResponse

    return discord.Forbidden(MockResponse(), "forbidden")
