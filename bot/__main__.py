import asyncio
from logging import DEBUG, ERROR, basicConfig, getLogger
from os import getenv

from dotenv import load_dotenv

from bot.core import Client

_log = getLogger()


def initialize_logging() -> None:
    """Configure logger handlers and formatters."""
    basicConfig(level=DEBUG)
    getLogger("discord").setLevel(ERROR)
    getLogger("discord.http").setLevel(ERROR)


async def main(token_var: str) -> None:
    """Initialize and run the client.

    Parameters
    ----------
    `token_var`: str - the environment value to pull the token from

    A token must be stored within an environment variable either in the system
    or within an .env file in the directory.

    The client is then created and ran with the collected token.

    """
    _log.debug("Hello from pyhnix")

    load_dotenv()
    if (token := getenv(token_var, None)) is None:
        raise Exception(f"No token found in environment variable: {token_var}")

    client = Client()
    try:
        await client.start(token=token)
    except Exception:
        _log.exception("A critical failure occured.")
    finally:
        await client.close()
        _log.info("Client closed, ending.")


if __name__ == "__main__":
    initialize_logging()
    asyncio.run(main("DISCORD_TOKEN"))
