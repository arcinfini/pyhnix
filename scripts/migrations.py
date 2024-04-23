import asyncio, os
from pathlib import Path
from asyncpg import connect, Connection, InvalidCatalogNameError

class Migration:

    def __init__(self, **kwargs) -> None:
        self.__connection: Connection | None = None
        self.kwargs = kwargs

    async def connection(self) -> Connection:
        if self.__connection is None:
            try:
                self.__connection = await connect(
                    **self.kwargs, 
                    database="__migrations"
                )
            except InvalidCatalogNameError:
                connection: Connection = await connect(
                    **self.kwargs,
                    database="template1"
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
    
    async def completed_migrations(self, database:str) -> list:
        conn = await self.connection()

        fetch = await conn.fetch("SELECT * FROM migrations WHERE database=$1;", database)
        results = [r['name'] for r in fetch]
        return results
    
    async def complete_migration(self, file: Path, database: str):
        conn = await self.connection()
        await conn.execute("INSERT INTO migrations (name, database) VALUES ($1, $2)", file.name, database)
    
class Database:
    
    def __init__(self, **kwargs) -> None:
        self.__connection: Connection | None = None
        self.kwargs = kwargs

    async def connection(self) -> Connection:
        if self.__connection is None:
        
            self.__connection = await connect(
                **self.kwargs
            )

        return self.__connection
    
    async def migrate(self, file: Path):
        """
        attempt a migration

        run in a transaction and rollback if failed migration
        """
        conn = await self.connection()
        async with conn.transaction():
            with open(file, 'r') as f:
                await conn.execute("".join(f.readlines()))

async def main(dbname, **kwargs):
    print("build migrations")
    migrator = Migration(**kwargs)
    database = Database(database=dbname, **kwargs)

    completed = await migrator.completed_migrations(dbname)
    print(completed)

    # collect already completed migrations
    # walk the migrations dir
    # complete migrations in order if not in completed migrations
    # when a migration is complete, add it into the migrations database and submit a transaction
    # move to the next migration
    migrations = Path('migrations')
    
    for file in migrations.iterdir():
        print(file.absolute())
        if file.name in completed:
            print("passing file")
            continue

        print("migrating")
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
        dbname=os.getenv("POSTGRES_DB")
    )

    asyncio.run(coro)