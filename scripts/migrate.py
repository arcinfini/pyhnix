from asyncio import run
from logging import getLogger
from os import getenv
from pathlib import Path

import asyncpg
from asyncpg import connect
from dotenv import load_dotenv

_log = getLogger(__name__)


class Migrator:
    """Handle the migrations between database changes."""

    def __init__(
        self,
        database: str,
        username: str,
        password: str,
        host: str = "localhost",
        port: int = 5432,
    ) -> None:
        self.__conn_kwargs = {
            "database": database,
            "user": username,
            "password": password,
            "host": host,
            "port": port,
        }
        self.__connection: asyncpg.Connection | None = None

    async def close(self) -> None:
        """Close the connection if it exists."""
        if self.__connection is not None:
            await self.__connection.close()

    async def __get_connection(self) -> asyncpg.Connection:
        """Get the connection or creates it."""
        if (
            self.__connection is not None
            and self.__connection.is_closed is False
        ):
            return self.__connection

        conn = await connect(**self.__conn_kwargs)
        self.__connection = conn

        await conn.execute(
            """
            CREATE SCHEMA IF NOT EXISTS __arc_migrations;
            CREATE TABLE IF NOT EXISTS __arc_migrations.__migrations (
                file_name TEXT,
                date TIMESTAMP DEFAULT NOW()
            );
            """
        )

        return conn

    async def fetch_migrations(self) -> list:
        """Fetch the migrations that have been completed."""
        conn = await self.__get_connection()

        results = await conn.fetch(
            "SELECT * FROM __arc_migrations.__migrations;"
        )
        return [r["file_name"] for r in results]

    async def do_migration(self, file: Path) -> None:
        """Do the migration for a file."""
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
            migrator = await self.__get_connection()
            await migrator.execute(
                """
                INSERT INTO __arc_migrations.__migrations
                (file_name)
                VALUES ($1)
                """,
                file.name,
            )


async def main() -> None:
    """Run the migrator."""
    load_dotenv()
    migrator = Migrator(
        database=getenv("POSTGRES_DB") or "",
        username=getenv("POSTGRES_USER") or "",
        password=getenv("POSTGRES_PASSWORD") or "",
        host=getenv("POSTGRES_HOST") or "",
        port=5432,
    )
    migration_scripts = Path("migrations")
    migrations = await migrator.fetch_migrations()

    for file in migration_scripts.iterdir():
        if file.name not in migrations:
            _log.debug("proceeding with migration %s", file)
            await migrator.do_migration(file)
        else:
            _log.debug("migration already issued %s", file)

    await migrator.close()


if __name__ == "__main__":
    run(main())
