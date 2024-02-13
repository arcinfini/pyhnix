import argparse, logging, os
from logging import handlers

from tomlkit import load as tomlload
from dotenv import load_dotenv
from rich.logging import RichHandler

from internal import client


def parse_args():
    parser = argparse.ArgumentParser(description="runs the club pybot : pyhnix")
    parser.add_argument(
        "--beta",
        "-b",
        action="store_true",
        help="enables the beta build",
        dest="beta",
    )
    parser.add_argument(
        "--debug", "-D", default=False, action="store_true", dest="debug"
    )

    return parser.parse_args()


def logger_setup(args):
    """
    Current Logger configuration:

    logs are stored in the `.records` directory within the project files.
    default discord logs are ignored and errors are propogated to the output
    stream.

    there are two handlers: the rich handler and the rotating file handler. it
    currently prints out to the stream a date, time and message desplaying the
    info of the log.

    debug mode can be enabled if the --debug flag is specified when running the
    initial script.
    """

    if not os.path.isdir(".records"):
        os.mkdir(".records")

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    logging.getLogger("discord").setLevel(logging.ERROR)
    logging.getLogger("discord.http").setLevel(logging.ERROR)

    console_handler = RichHandler()
    console_formatter = logging.Formatter(
        "%(name)-25s: %(levelname)-8s %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    file_handler = handlers.TimedRotatingFileHandler(
        ".records/record.txt", when="D", utc=True
    )
    file_formatter = logging.Formatter(
        "[%(asctime)s] | [%(levelno)s]: %(name)s > %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S ()",
    )
    file_handler.setFormatter(file_formatter)

    if args.debug:
        root.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)

    root.addHandler(console_handler)
    root.addHandler(file_handler)


def main():
    args = parse_args()
    logger_setup(args)

    with open("production.toml", "r") as file:
        config = tomlload(file)

    bot = client.Phoenix(config=config)

    if (token := os.getenv(config["token-var"])) is None:  # type: ignore
        raise Exception(
            "Missing bot token in argument: %s" % config["token-var"]
        )

    bot.run(token)


if __name__ == "__main__":
    main()
