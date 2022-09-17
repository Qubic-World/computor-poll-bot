
import logging
from typing import Union
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


def get_poll_channel_id() -> int:
    return int(getenv("POLL_CHANNEL_ID", None))


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


async def get_messages_from_poll_channel(bot: Client) -> Union[list[Message], None]:
    channel = get_poll_channel(bot)
    if channel is None:
        return

    async for message in channel.history():
        yield message


async def get_poll_message_by_id(bot: Client, message_id: int) -> Message:
    channel = get_poll_channel(bot)
    return await channel.fetch_message(message_id)


def get_poll_channel(bot: Client):
    return bot.get_channel(get_poll_channel_id())


def get_components_by_type(message, component_type):
    import itertools
    from discord import ActionRow, Message

    if not isinstance(message, Message):
        logging.exception(TypeError('message is not discord.Message'))
        return []

    return list(itertools.chain.from_iterable([[component for component in row.children if isinstance(component, component_type)]
                                               for row in message.components if isinstance(row, ActionRow)]))


def get_buttons_from_message(message):
    from discord import Button
    return get_components_by_type(message=message, component_type=Button)
