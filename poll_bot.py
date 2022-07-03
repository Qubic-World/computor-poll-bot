import asyncio
import os

from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv

from commands.pool import PoolCommands
from role import RoleManager
from data.identity import IdentityManager
from data.users import UserData
from utils.broadcastcomputors import broadcast_loop
from utils.message import (get_identity_list, get_user_id_from_message, is_valid_identity,
                            is_valid_message)
from verify.user import is_existing_user

intents = Intents.default()
intents.members = True
intents.messages = True
poll_bot = commands.Bot(command_prefix="/", intents=intents)

pool_commands = PoolCommands()
user_data = UserData()
identity_manager = IdentityManager()
role_manager = RoleManager(user_data, poll_bot)


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


@poll_bot.command()
async def add_identity(ctx, *identity):
    valid_id = [item for item in list(identity) if is_valid_identity(item)]
    if len(valid_id) > 0:
        identity_manager.apply_identity(set(valid_id))
        await identity_manager.save_to_file()


def main():
    # Read from .env
    load_dotenv()

    token = os.environ.get("BOT_ACCESS_TOKEN")
    loop = asyncio.get_event_loop()

    # Loading data
    loop.run_until_complete(asyncio.gather(
        user_data.load_from_file(), identity_manager.load_from_file()))

    identity_manager.observe_added(role_manager.add_role)
    identity_manager.observe_removed(role_manager.remove_role)
    
    try:
        # Running pool of commands
        pool_commands.start()

        broadcast_computors_task = loop.create_task(broadcast_loop(identity_manager))

        # Running the bot
        task = loop.create_task(poll_bot.start(
            token, bot=True, reconnect=True))
        del token
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        print("Waiting for the tasks in the pool to be completed")
        loop.run_until_complete(pool_commands.stop())
        loop.run_until_complete(identity_manager.stop())
        loop.run_until_complete(poll_bot.close())
        broadcast_computors_task.cancel()
        try:
            loop.run_until_complete(broadcast_computors_task)
        except asyncio.CancelledError:
            pass
    finally:
        loop.close()


if __name__ == "__main__":
    main()
