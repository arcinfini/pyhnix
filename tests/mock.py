from unittest.mock import MagicMock, Mock

import discord


class ErrorMock(MagicMock, discord.DiscordException):
    pass


class Client(Mock):
    pass


class Guild(Mock):
    spec = discord.Guild


class Role(Mock):
    pass


class User(Mock):
    spec = discord.User


class Member(Mock):
    spec = discord.Member


class Message(Mock):
    pass
