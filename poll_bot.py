import asyncio
import os

from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv

from commands.pool import PoolCommands
from qubic.manager import QubicNetworkManager
from role import RoleManager
from data.identity import identity_manager
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

        # broadcast_computors_task = loop.create_task(
        #     broadcast_loop(identity_manager))

        network = QubicNetworkManager(["213.127.147.70",
                                    "83.57.175.137",
                                    "178.172.194.130",
                                    "82.114.88.225",
                                    "82.223.197.126",
                                    "82.223.165.100",
                                    "85.215.98.91",
                                    "212.227.149.43"])

        network_task = loop.create_task(network.start())
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
        loop.run_until_complete(network.stop())
        if not network_task.cancelled():
            network_task.cancel()
        # # broadcast_computors_task.cancel()
        try:
            loop.run_until_complete(network_task)
        except asyncio.CancelledError:
            pass
    finally:
        if not loop.is_closed():
            loop.close()


if __name__ == "__main__":
    main()
