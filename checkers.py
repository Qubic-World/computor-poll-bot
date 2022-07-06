
from utils.botutils import get_channel_id, get_role, get_role_by_context, get_role_name
from discord.ext import commands


async def is_valid_channel(ctx):
    return ctx.message.channel.id == get_channel_id()

async def is_valid_role(ctx: commands.Context):
    result = False
    try:
        result = get_role_by_context(ctx) != None
    except:
       result = False
    finally:
        if result == False:
            await ctx.reply(f"Can't get the `{get_role_name()}` role to execute your request") 
        return result