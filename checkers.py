
from discord import User
from discord.ext.commands import Context
from discord.utils import get

from utils.botutils import (get_channel_id, get_guild, get_guild_id,
                            get_poll_channel_id, get_role, get_role_by_context,
                            get_role_name)


async def is_bot_channel(ctx):
    return ctx.message.channel.id == get_channel_id()


async def is_bot_in_guild(ctx: Context):
    """Whether the bot is running in the right guild
    """
    return get_guild(ctx.bot) != None


async def is_user_in_guild(ctx: Context):
    """Whether the user belongs to the guild the bot is in
    """
    user = ctx.author
    if isinstance(user, User) == False:
        return False

    result = get(user.mutual_guilds, id=get_guild_id()) != None
    if result == False:
        guild = get_guild(ctx.bot)
        await ctx.send(f"You are not a member of {guild.name}")

    return result


async def is_poll_channel(ctx):
    return ctx.message.channel.id == get_poll_channel_id()


async def has_role_in_guild(ctx):
    """If no role is found on the server Commands will not be executed
    """
    result = False
    try:
        result = get_role(ctx.bot) != None
    except:
        result = False
    finally:
        if result == False:
            await ctx.reply(f"Can't get the `{get_role_name()}` role to execute your request")
        return result


async def has_role_on_member(ctx):
    role_name = get_role_name()
    if len(role_name) <= 0:
        await ctx.reply("Could not find the role on the server")
        return

    result = role_name in [role.name for role in ctx.author.roles]
    if result == False:
        await ctx.reply(f"You do not have a {role_name} role to execute this command")

    return result
