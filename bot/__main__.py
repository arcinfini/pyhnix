import argparse
import asyncio
from logging import DEBUG, ERROR, INFO, basicConfig, getLogger
from os import getenv

from dotenv import load_dotenv

from bot.core import Client
from bot.util import Mode

_log = getLogger()


def parser() -> argparse.ArgumentParser:
    """Configure the argument parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--mode",
        nargs="?",
        default="dev",
        choices=["dev", "prod"],
        type=Mode.from_str,
    )
    parser.add_argument("-t", "--token-var", nargs="?", default="DISCORD_TOKEN")

    return parser


def initialize_logging(args: argparse.Namespace) -> None:
    """Configure logger handlers and formatters."""
    level = DEBUG if args.mode == Mode.DEV else INFO

    basicConfig(level=level)
    getLogger("discord").setLevel(ERROR)
    getLogger("discord.http").setLevel(ERROR)


async def main(args: argparse.Namespace) -> None:
    """Initialize and run the client.

    Parameters
    ----------
    args: `argparse.Namespace`
        A namespace of the parsed arguments supplied to the executable

    A token must be stored within an environment variable either in the system
    or within an .env file in the directory.

    The client is then created and ran with the collected token.

    """
    _log.debug("Hello from pyhnix")

    load_dotenv()
    if (token := getenv(args.token_var, None)) is None:
        raise Exception(
            f"No token found in environment variable: {args.token_var}"
        )

    client = Client(args)
    try:
        await client.start(token=token)
    except Exception:
        _log.exception("A critical failure occured.")
    finally:
        await client.close()
        _log.info("Client closed, ending.")


if __name__ == "__main__":
    args = parser().parse_args()
    initialize_logging(args)
    asyncio.run(main(args))
