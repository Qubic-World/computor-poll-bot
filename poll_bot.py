import asyncio
import os

from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv

from commands.pool import PoolCommands
from qubic.manager import QubicNetworkManager
from qubic.qubicutils import load_cache_computors
from role import RoleManager
from data.identity import identity_manager
from data.users import UserData
from utils.botutils import get_channel_id, get_role_by_id
from utils.message import (get_identity_list, get_user_id_from_message,
                           is_valid_message)
from verify.user import is_existing_user

intents = Intents.default()
intents.members = True
intents.messages = True
poll_bot = commands.Bot(command_prefix="/", intents=intents)

pool_commands = PoolCommands()
user_data = UserData()
role_manager = RoleManager(user_data, poll_bot)


async def is_valid_channel(ctx):
    return ctx.message.channel.id == get_channel_id()


@poll_bot.command(name='register')
@commands.check(is_valid_channel)
# Adding to the pool
async def _register(ctx, *, json):
    await pool_commands.add_command(register, ctx, json)

# Executing from pool
async def register(ctx: commands.Context, json):
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

@poll_bot.command(name="roles")
@commands.check(is_valid_channel)
async def _roles(ctx):
    await pool_commands.add_command(roles, ctx)

async def roles(ctx: commands.Context):
    await ctx.channel.send(", ".join([str(f"Name: {r.name}, ID: {r.id}") for r in ctx.guild.roles]))


@poll_bot.event
async def on_ready():
    print("On ready")


def main():
    # Read from .env
    load_dotenv()

    # Creating folder for files
    if not os.path.isdir("data_files"):
        os.mkdir("data_files")
    

    token = os.environ.get("BOT_ACCESS_TOKEN")
    loop = asyncio.get_event_loop()

    # Loading computors
    loop.run_until_complete(load_cache_computors())

    # Loading user data and identities
    loop.run_until_complete(asyncio.gather(
        user_data.load_from_file(), identity_manager.load_from_file()))

    # Setting identity manager
    identity_manager.observe_added(role_manager.add_role)
    identity_manager.observe_removed(role_manager.remove_role)

    try:
        # Running pool of commands
        pool_commands.start()

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
