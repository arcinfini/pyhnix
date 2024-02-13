import asyncio
import logging
import os

from bot.client import Phoenix


def logger_setup() -> None:
    """Set up the current logger configuration.

    logs are stored in the `.records` directory within the project files.
    default discord logs are ignored and errors are propogated to the output
    stream.

    there are two handlers: the rich handler and the rotating file handler. it
    currently prints out to the stream a date, time and message desplaying the
    info of the log.
    """
    from logging.handlers import TimedRotatingFileHandler as TimedFileHandler

    from rich.logging import RichHandler

    # https://docs.python.org/3/library/logging.handlers.html#logging.handlers.RotatingFileHandler

    if not os.path.isdir(".records"):
        os.mkdir(".records")

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    logging.getLogger("discord").setLevel(logging.ERROR)
    logging.getLogger("discord.http").setLevel(logging.ERROR)

    handlers = [
        TimedFileHandler(".records/record.txt", when="D", utc=True),
        RichHandler(),
    ]

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] | [%(levelname)-8s]: %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


async def main() -> None:
    """Build and run the client."""
    client = Phoenix()

    if (token := os.getenv("PYHNIX_TOKEN")) is None:
        raise Exception("Bot token not found in PYHNIX_TOKEN env variable")

    await client.login(token)
    await client.connect()


if __name__ == "__main__":
    logger_setup()

    asyncio.run(main())
