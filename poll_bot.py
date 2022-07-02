import asyncio
import os

from discord.ext import commands
from dotenv import load_dotenv

from commands.pool import PoolCommands
from verify.message import get_username_id_from_message, is_valid_message
from verify.user import is_existing_user

poll_bot = commands.Bot(command_prefix="/")
pool = PoolCommands()


@poll_bot.command(name='register')
# Adding to the pool
async def _register(ctx, *, json):
    await pool.add_command(register, ctx, json)

# Executing from pool
async def register(ctx, json):
    result = is_valid_message(json)
    if result[0] == False:
        await ctx.reply(result[1])
        return

    username_id = get_username_id_from_message(json)

    username_result = await is_existing_user(poll_bot, username_id)
    if username_result[0] == False:
        await ctx.reply("No such user could be found")
        return

    await ctx.reply(f"User {username_result[1]} added")


@poll_bot.event
async def on_ready():
    print("On ready")


def main():
    # Read from .env
    load_dotenv()

    token = os.environ.get("BOT_ACCESS_TOKEN")
    loop = asyncio.get_event_loop()

    try:
        pool.start()
        loop.run_until_complete(poll_bot.start(
            token, bot=True, reconnect=True))
    except KeyboardInterrupt:
        print("Waiting for the tasks in the pool to be completed")
        loop.run_until_complete(pool.stop())
        loop.run_until_complete(poll_bot.close())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
