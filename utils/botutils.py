
import logging
from discord import Client, Member, Message
from discord.utils import get
from discord.ext import commands
from os import getenv


def get_channel_id() -> int:
    return int(getenv("CHANNEL_ID"))


def get_member_by_id(poll_bot: Client, user_id: int):
    guild = get_guild(poll_bot)
    for member in guild.members:
        if member.id == user_id:
            return member

    return None

def get_guild_id():
    try:
        return int(getenv("GUILD_ID"))
    except Exception as e:
        logging.error(e)
        return -1


def get_guild(poll_bot: Client):
    return poll_bot.get_guild(get_guild_id())

def get_guild_by_member(member: Member):
    return member.guild


def get_role_name() -> str:
    try:
        return getenv("ROLE_NAME")
    except Exception as e:
        logging.error(e)
        return ""


def get_role(poll_bot: Client):
    return get(get_guild(poll_bot).roles, name=get_role_name())

def get_role_by_context(ctx: commands.Context):
    return get(ctx.guild.roles, name=get_role_name())

def get_username_with_discr(member: Member) -> str:
    """Returns username#4444
    """
    return str(member.name + '#' + member.discriminator)


async def get_message_by_id(bot: Client, message_id:int) -> Message:
    channel = bot.get_channel(get_channel_id())
    return await channel.fetch_message(message_id)