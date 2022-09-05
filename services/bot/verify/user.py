import re
from discord import Client, User, Member

from utils.botutils import get_guild, get_username_with_discr

USERNAME_RE = re.compile(r".+\#\d{4}")


def is_valid_user(username_id: str):
    if username_id.isdigit() == False:
        return (False, "Username ID should only consist of numbers")

    return (True, "")


def get_member_by_username(client: Client, username: str) -> Member:
    if USERNAME_RE.match(username) == None:
        raise ValueError("Username should be: name#4444")

    for member in get_guild(client).members:
        member_name = get_username_with_discr(member)
        if member_name == username:
            return member

    return None


def get_user_id_from_username(client: Client, username: str) -> int:
    member = get_member_by_username(client, username)
    if member != None:
        return member.id

    return None
