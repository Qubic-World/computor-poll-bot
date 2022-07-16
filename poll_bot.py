import asyncio
import os
from typing import Optional

from discord import Intents
from discord.ext import commands
from discord_components import DiscordComponents
from dotenv import load_dotenv

from checkers import has_role_in_guild, is_bot_in_guild, is_user_in_guild
from commands.pool import pool_commands
from commands.register import RegisterCog
from data.identity import identity_manager
from data.users import user_data
from poll.pollmanager import PollCog
from qubic.manager import QubicNetworkManager
from qubic.qubicutils import load_cache_computors
from role import RoleManager

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


@poll_bot.event
async def on_ready():
    print("On ready")

    poll_cog = PollCog(poll_bot)
    register_cog = RegisterCog(poll_bot)
    await poll_cog._load_polls_from_file()
    poll_bot.add_cog(poll_cog)
    poll_bot.add_cog(register_cog)

    # Setting identity manager
    identity_manager.add_new_identities_callback(role_manager.reassign_roles)
    identity_manager.add_new_identities_callback(poll_cog.recount)
    identity_manager.add_removed_identities_callback(
        role_manager.reassign_roles)
    identity_manager.add_removed_identities_callback(poll_cog.recount)

    user_data.add_new_identities_callback(role_manager.reassing_role)
    user_data.add_new_identities_callback(poll_cog.recount)
    user_data.add_removed_identities_callback(role_manager.reassing_role)
    user_data.add_removed_identities_callback(poll_cog.recount)

    # After starting the bot, reassign the roles
    await role_manager.reassign_roles()

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

    poll_bot.add_check(is_bot_in_guild)
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
