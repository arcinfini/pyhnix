from unittest.mock import AsyncMock, patch

import pytest
from asyncpg import Connection, InvalidCatalogNameError

from bot.utils.migration import Migrator


@pytest.mark.asyncio
@patch("bot.utils.migration.connect", new_callable=AsyncMock)
async def test_get_migrator(mock_connect: AsyncMock) -> None:
    """Test getting the connection to the migrator.

    Create a mock connection and a mock method for asyncpg.connect. Since the
    function is imported using a `from` statement, the path to the function
    within the file needs to be specifically defined. Afterwards assure that the
    connect function was called and the execute was called once
    """
    mock_conn = AsyncMock(spec=Connection)
    mock_connect.return_value = mock_conn

    migrator = Migrator(database="test_db", user="user")
    conn = await migrator._Migrator__get_migrator()  # type: ignore [attr-defined]

    assert conn is not None
    mock_connect.assert_called()
    mock_conn.execute.assert_called_once()


@pytest.mark.asyncio
@patch("bot.utils.migration.connect", new_callable=AsyncMock)
@patch(
    "bot.utils.migration.Migrator._Migrator__try_get_migrator",
    new_callable=AsyncMock,
)
async def test_get_migrator_new(
    mock_try_get_migrator: AsyncMock, mock_connect: AsyncMock
) -> None:
    """Test getting the connection to the migrator for the first time.

    DOC ME
    """
    mock_conn = AsyncMock(spec=Connection)
    mock_connect.return_value = mock_conn

    mock_try_get_migrator.side_effect = [
        InvalidCatalogNameError(
            "no __migrations"
        ),  # test to make sure it throws
        InvalidCatalogNameError("no __migrations"),  # for logic test
        mock_conn,
    ]

    migrator = Migrator(database="test_db", user="user")

    # Test mock try_get_migrator is working
    with pytest.raises(InvalidCatalogNameError):
        await migrator._Migrator__try_get_migrator()  # type: ignore [attr-defined]
    mock_try_get_migrator.assert_called_once()
    mock_try_get_migrator.reset_mock()

    # Test try_get_migrator is called twice
    # and verify that execute is called twice. Once for the database creation
    # and once for creating the table

    conn = await migrator._Migrator__get_migrator()  # type: ignore [attr-defined]
    assert conn is not None

    assert mock_try_get_migrator.call_count == 2
    assert mock_conn.execute.call_count == 2


@pytest.mark.asyncio
@patch(
    "bot.utils.migration.Migrator._Migrator__get_migrator",
    new_callable=AsyncMock,
)
async def test_get_migrations(mock_get_migrator: AsyncMock) -> None:
    """Test getting migrations.

    Create a mock method for __get_migrator. set the return value for the mock
    method to a mock connection value. Then simulate the response to a single
    entry of a database migration.
    """
    mock_conn = AsyncMock()
    mock_get_migrator.return_value = mock_conn
    mock_conn.fetch.return_value = [
        {"name": "migration_001.sql", "database": "test_db"}
    ]

    migrator = Migrator(
        database="test_db"
    )  # The connection values do not matter here
    migrations = await migrator.get_migrations()

    assert migrations == ["migration_001.sql"]
    mock_conn.fetch.assert_called_once()


# # Tests for do_migration method
# async def test_do_migration_success():
#     with patch('asyncpg.connect', new_callable=AsyncMock) as mock_connect, \
#          patch('builtins.open', new_callable=pytest.mock.mock_open, read_data="SQL SCRIPT") as mock_file:
#         mock_conn = AsyncMock()
#         mock_connect.return_value = mock_conn
#         migrator = Migrator(database='test_db')
#         await migrator.do_migration(Path("/fake/path/migration_001.sql"))
#         mock_conn.execute.assert_called()
#         mock_file.assert_called_with("/fake/path/migration_001.sql")
#         # Assert transaction is started and migration is logged
#         mock_conn.transaction.assert_called()

# # Test handling connection failures or script errors
# async def test_do_migration_fail():
#     with patch('asyncpg.connect', new_callable=AsyncMock) as mock_connect, \
#          patch('builtins.open', new_callable=pytest.mock.mock_open, read_data="SQL SCRIPT") as mock_file, \
#          patch('your_module._log') as mock_logger:
#         mock_conn = AsyncMock()
#         mock_conn.execute.side_effect = Exception("DB Error")
#         mock_connect.return_value = mock_conn
#         migrator = Migrator(database='test_db')

#         with pytest.raises(SystemExit):  # Expecting SystemExit due to exit(1) in the code
#             await migrator.do_migration(Path("/fake/path/migration_001.sql"))
#         mock_logger.exception.assert_called_once_with("Migration failed for %s", Path("/fake/path/migration_001.sql"))
