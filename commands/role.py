from os import getenv

from discord import Guild, Member


async def switch_role(guild: Guild, member: Member, add: bool = True):
    if member.bot:
        raise ValueError("you cannot assign a role to the bot")

    try:
        role = guild.get_role(int(getenv("ROLE_ID")))
        if add:
            await member.add_roles(role)
        else:
            await member.remove_roles(role)
    finally:
        pass
