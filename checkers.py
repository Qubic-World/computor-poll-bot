
from utils.botutils import get_channel_id, get_role, get_role_by_context, get_role_name
from discord.ext import commands


async def is_valid_channel(ctx):
    return ctx.message.channel.id == get_channel_id()


async def has_role_in_guild(ctx):
    """If no role is found on the server Commands will not be executed
    """
    result = False
    try:
        result = get_role_by_context(ctx) != None
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
