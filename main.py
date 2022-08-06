
import argparse
import asyncio
import discord

from internal import client

def parse_args():
    parser = argparse.ArgumentParser(description="runs the club pybot")
    parser.add_argument('--token', '-t', default='MAIN_BOT_TOKEN', help='the environment variable where the bot token is stored', dest='token')
    parser.add_argument('--guild', '--server', '-g', type=int, default=970761243277266944, help='the id of the guild used for testing', dest='guild')
    parser.add_argument('--prefix', '-p', default='!', help='the command prefix to listen for; defaults to "!"', dest='prefix')
    parser.add_argument('--beta', '-b', action='store_true', help='enables the beta build', dest='beta')
    parser.add_argument('--database', '-d', type=str, default='elonesports', help='the database in mongodb to use; defaults to "elonesports"', dest='database')

    return parser.parse_args()

async def main():

    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    
    bot = client.Phoenix(intents=intents, namespace=parse_args())
    
    await bot.load_extensions("ext")
    await bot.run("MAIN_TOKEN")

if __name__ == "__main__":
    asyncio.run(main())