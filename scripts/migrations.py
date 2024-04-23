import asyncio
import os
from logging import getLogger
from pathlib import Path

from asyncpg import Connection, InvalidCatalogNameError, connect

_log = getLogger(__name__)


class Migration:
    """The class that handles migration data."""

    def __init__(self, **kwargs) -> None:  # type: ignore [no-untyped-def] # noqa: ANN003
        self.__connection: Connection | None = None
        self.kwargs = kwargs

    async def connection(self) -> Connection:
        """Connect to the __migrations database and create if not existing."""
        if self.__connection is None:
            try:
                self.__connection = await connect(
                    **self.kwargs, database="__migrations"
                )
            except InvalidCatalogNameError:
                connection: Connection = await connect(
                    **self.kwargs, database="template1"
                )

                await connection.execute("CREATE DATABASE __migrations;")
                await connection.close()
                self.__connection = await self.connection()

            await self.__connection.execute(
                """
                CREATE TABLE IF NOT EXISTS migrations (
                    name TEXT NOT NULL,
                    database TEXT NOT NULL
                );
                """
            )

        return self.__connection

    async def completed_migrations(self, database: str) -> list:
        """Fetch migrations that have already been completed."""
        conn = await self.connection()

        results = await conn.fetch(
            "SELECT * FROM migrations WHERE database=$1;", database
        )
        return [r["name"] for r in results]

    async def complete_migration(self, file: Path, database: str) -> None:
        """Store a migration log in the __migrations database."""
        conn = await self.connection()
        await conn.execute(
            "INSERT INTO migrations (name, database) VALUES ($1, $2)",
            file.name,
            database,
        )


class Database:
    """The database that is being migrated."""

    def __init__(self, **kwargs) -> None:  # type: ignore [no-untyped-def] # noqa: ANN003
        self.__connection: Connection | None = None
        self.kwargs = kwargs

    async def connection(self) -> Connection:
        """Connect to the database that is being migrated."""
        if self.__connection is None:
            self.__connection = await connect(**self.kwargs)

        return self.__connection

    async def migrate(self, file: Path) -> None:
        """Attempt a migration.

        Run in a transaction and rollback if the migration failed. Do not catch
        as later migrations rely on the success of the previous migrations.
        """
        conn = await self.connection()
        async with conn.transaction():
            with open(file) as f:
                await conn.execute("".join(f.readlines()))


async def main(dbname: str | None, **kwargs) -> None:  # type: ignore [no-untyped-def] # noqa: ANN003
    """Run the migration script."""
    if dbname is None:
        raise Exception("missing POSTGRES_DB enviornment variable")

    _log.debug("build migrations")
    migrator = Migration(**kwargs)
    database = Database(database=dbname, **kwargs)

    completed = await migrator.completed_migrations(dbname)
    _log.debug(completed)

    migrations = Path("migrations")

    for file in migrations.iterdir():
        _log.debug(file.absolute())
        if file.name in completed:
            _log.debug("passing file")
            continue

        _log.debug("migrating")
        await database.migrate(file)
        await migrator.complete_migration(file, dbname)


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()

    coro = main(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=5432,
        dbname=os.getenv("POSTGRES_DB"),
    )

    asyncio.run(coro)
