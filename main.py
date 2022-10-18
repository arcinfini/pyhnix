
import argparse, logging, os
from logging import handlers

from dotenv import load_dotenv
from rich.logging import RichHandler

from internal import client

def parse_args():
    parser = argparse.ArgumentParser(description="runs the club pybot : pyhnix")
    parser.add_argument('--token', '-t', default='MAIN_BOT_TOKEN', help='the environment variable where the bot token is stored', dest='token')
    parser.add_argument('--guild', '--server', '-g', type=int, default=970761243277266944, help='the id of the guild used for testing', dest='guild')
    parser.add_argument('--prefix', '-p', default='!', help='the command prefix to listen for; defaults to "!"', dest='prefix')
    parser.add_argument('--beta', '-b', action='store_true', help='enables the beta build', dest='beta')
    parser.add_argument('--database', '-d', type=str, default='POSTGRES_DB', help='the environment variable where the database name is stored; defaults to "POSTGRES_DB"', dest='database')
    parser.add_argument('--debug', '-D', default=False, action='store_true', dest='debug')
    parser.add_argument('--host', default='pyhnix-postgres', dest='host')

    return parser.parse_args()

def logger_setup(args):
    if not os.path.isdir(".records"):
        os.mkdir(".records")
    
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    logging.getLogger("discord").setLevel(logging.ERROR)
    logging.getLogger("discord.http").setLevel(logging.ERROR)

    console_handler = RichHandler()
    console_formatter = logging.Formatter("%(name)-25s: %(levelname)-8s %(message)s")
    console_handler.setFormatter(console_formatter)

    file_handler = handlers.TimedRotatingFileHandler(
        ".records/record.txt", 
        when="D", utc=True
    )
    file_formatter = logging.Formatter(
        "[%(asctime)s] | [%(levelno)s]: %(name)s > %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S ()"
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

    if args.beta: load_dotenv()
    
    bot = client.Phoenix(namespace=args)
    
    bot.run(os.getenv(args.token))

if __name__ == "__main__":
    main()