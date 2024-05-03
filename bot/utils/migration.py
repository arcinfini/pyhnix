from logging import getLogger
from pathlib import Path

from asyncpg import Connection, InvalidCatalogNameError, connect

_log = getLogger(__name__)


class Migrator:
    """The class that handles migration data."""

    def __init__(self, **kwargs) -> None:  # type: ignore [no-untyped-def] # noqa: ANN003
        self.__connection: Connection | None = None
        self.__migrator: Connection | None = None
        self.kwargs = kwargs
        self.database: str = kwargs.pop("database")

    async def __try_get_migrator(self) -> Connection:
        """Try to get the __migration database.

        Raises InvalidCatalogNameError if it does not exist.
        """
        return await connect(**self.kwargs, database="__migrations")

    async def __create_migrator(self) -> Connection:
        """Create the __migrations database if it does not exist."""
        connection: Connection = await connect(
            **self.kwargs, database="template1"
        )

        await connection.execute("CREATE DATABASE __migrations;")
        await connection.close()

        self.__migrator = await self.__try_get_migrator()
        return self.__migrator

    async def __get_migrator(self) -> Connection:
        """Connect to the __migrations database and create if not existing."""
        if self.__migrator is None:
            try:
                self.__migrator = await self.__try_get_migrator()
            except InvalidCatalogNameError:
                self.__migrator = await self.__create_migrator()

            await self.__migrator.execute(
                """
                CREATE TABLE IF NOT EXISTS migrations (
                    name TEXT NOT NULL,
                    database TEXT NOT NULL
                );
                """
            )

        return self.__migrator

    async def __get_connection(self) -> Connection:
        """Connect to the database that is being migrated."""
        if self.__connection is None:
            self.__connection = await connect(
                **self.kwargs, database=self.database
            )

        return self.__connection

    async def get_migrations(self) -> list:
        """Fetch migrations that have already been completed."""
        conn = await self.__get_migrator()

        results = await conn.fetch(
            "SELECT * FROM migrations WHERE database=$1;", self.database
        )
        return [r["name"] for r in results]

    async def do_migration(self, file: Path) -> None:
        """Store a migration log in the __migrations database."""
        try:
            conn = await self.__get_connection()
            async with conn.transaction():
                with open(file) as f:
                    script = "".join(f.readlines())
                    _log.debug("%s: %s", file, script)

                    await conn.execute(script)
        except Exception:
            # Migration failed and program will error where database required
            # therefore execution should be aborted
            _log.exception("Migration failed for %s", file)
            exit(1)
        finally:
            migrator = await self.__get_migrator()
            await migrator.execute(
                "INSERT INTO migrations (name, database) VALUES ($1, $2)",
                file.name,
                self.database,
            )
