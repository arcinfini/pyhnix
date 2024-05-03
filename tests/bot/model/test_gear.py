from unittest.mock import AsyncMock, patch

import pytest
import tests.mock as mock

from bot.model.gear import Gear


@pytest.mark.asyncio
async def test_on_load_runs() -> None:
    with patch(
        "bot.model.gear.Gear.on_load", new_callable=AsyncMock
    ) as mock_on_load:
        client = mock.Client()
        gear = Gear(client)

        await gear.cog_load()
        mock_on_load.assert_called_once()
