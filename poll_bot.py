import asyncio
import os

from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv

from commands.pool import PoolCommands
from data.users import UserData
from verify.message import (get_identity_list, get_user_id_from_message,
                            is_valid_message)
from verify.user import is_existing_user

intents = Intents.default()
intents.members = True
intents.messages = True
poll_bot = commands.Bot(command_prefix="/", intents=intents)

pool_commands = PoolCommands()
user_data = UserData()


@poll_bot.command(name='register')
# Adding to the pool
async def _register(ctx, *, json):
    await pool_commands.add_command(register, ctx, json)

# Executing from pool
async def register(ctx, json):
    result = is_valid_message(json)
    if result[0] == False:
        await ctx.reply(result[1])
        return

    user_id = get_user_id_from_message(json)

    username_result = await is_existing_user(poll_bot, user_id)
    if username_result[0] == False:
        await ctx.reply("No such user could be found")
        return

    user_data.add_data(user_id, get_identity_list(json))
    await asyncio.gather(user_data.save_to_file(), ctx.reply(f"User {username_result[1]} added"))


@poll_bot.event
async def on_ready():
    print("On ready")


def main():
    # Read from .env
    load_dotenv()

    token = os.environ.get("BOT_ACCESS_TOKEN")
    loop = asyncio.get_event_loop()

    # Loading user data
    loop.run_until_complete(user_data.load_from_file())
    print(user_data._json_data)

    try:
        # Running pool of commands
        pool_commands.start()

        # Running the bot
        loop.run_until_complete(poll_bot.start(
            token, bot=True, reconnect=True))
    except KeyboardInterrupt:
        print("Waiting for the tasks in the pool to be completed")
        loop.run_until_complete(pool_commands.stop())
        loop.run_until_complete(poll_bot.close())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
