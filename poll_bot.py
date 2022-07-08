import asyncio
import os
from typing import Optional

from discord import Intents
from discord.ext import commands
from discord_components import DiscordComponents
from dotenv import load_dotenv


from poll.pollmanager import PollCog
from checkers import is_valid_channel, has_role_in_guild
from commands.pool import pool_commands
from data.identity import identity_manager
from data.users import user_data
from qubic.manager import QubicNetworkManager
from qubic.qubicutils import load_cache_computors
from role import RoleManager
from utils.botutils import get_username_with_discr
from utils.message import (get_identity_list, get_username_from_message,
                           is_valid_message)
from verify.user import get_member_by_username, get_user_id_from_username

"""Commands Bot
"""
intents = Intents.default()
intents.members = True
intents.messages = True
poll_bot = commands.Bot(command_prefix="/", intents=intents)
DiscordComponents(poll_bot)

"""Managers
"""
role_manager = RoleManager(user_data, poll_bot)


"""Qubic Network
"""
network = QubicNetworkManager(["213.127.147.70",
                               "83.57.175.137",
                               "178.172.194.130",
                               "82.114.88.225",
                               "82.223.197.126",
                               "82.223.165.100",
                               "85.215.98.91",
                               "212.227.149.43"])
network_task: Optional[asyncio.Task] = None


"""Commands
"""


@poll_bot.command(name='register')
@commands.check(is_valid_channel)
@commands.check(has_role_in_guild)
async def _register(ctx, *, json):
    """User registration
    """
    # Adding to the pool
    await pool_commands.add_command(register, ctx, json)

# Executing from pool


async def register(ctx: commands.Context, json):
    """User registration
    """
    result = is_valid_message(json)
    if result[0] == False:
        await ctx.reply(result[1])
        return

    username = get_username_from_message(json)
    if len(username) <= 0:
        await ctx.reply("Failed to retrieve username from message field")
        return

    member = get_member_by_username(poll_bot, username)
    error_message = ""
    if member == None:
        error_message = "Unable to find the user"
    elif get_username_with_discr(ctx.author) != username:
        error_message = "The request must include your username"

    if len(error_message) > 0:
        await ctx.reply(error_message)
        return

    try:
        message = str()
        user_id = get_user_id_from_username(poll_bot, username)
        if user_id == None:
            message = str("Unable to find the user")
    except ValueError as e:
        message = str("Error: " + str(e))
    finally:
        if len(message) > 0:
            await ctx.reply(message)
            return

    result = user_data.add_data(user_id, get_identity_list(json))
    if result[0] == False:
        await ctx.reply(result[1])
        return

    await asyncio.gather(user_data.save_to_file(), ctx.reply(f"User {username} added"))


@poll_bot.event
async def on_ready():
    print("On ready")

    poll_cog = PollCog(poll_bot)
    await poll_cog.load_from_cache()
    poll_bot.add_cog(poll_cog)

    # Starting qubic-netwrok
    network_task = asyncio.create_task(network.start())


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
    user_data.observe_new_identities(identity_manager.on_new_identities)

    poll_bot.add_check(is_valid_channel)
    poll_bot.add_check(has_role_in_guild)

    try:
        # Running pool of commands
        pool_commands.start()

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
        if network_task != None and not network_task.cancelled():
            network_task.cancel()
            try:
                loop.run_until_complete(network_task)
            except asyncio.CancelledError:
                pass
    finally:
        if not loop.is_closed():
            loop.close()


if __name__ == "__main__":
    main()
