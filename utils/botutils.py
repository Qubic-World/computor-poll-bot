
from discord import Client, Guild
from os import getenv


def get_channel_id() -> int:
    return int(getenv("CHANNEL_ID"))


def get_member_by_id(poll_bot: Client, user_id: str):
    for member in poll_bot.get_all_members():
        if member.id == int(user_id):
            return member

    return None


def get_channel(poll_bot: Client):
    return poll_bot.get_channel(get_channel_id())


def get_role(guild: Guild):
    return guild.get_role(int(getenv("ROLE_ID")))

def get_role_by_id(guild: Guild, id: int):
    return guild.get_role(id)
