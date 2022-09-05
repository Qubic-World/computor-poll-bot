import asyncio
import logging
import os

from checkers import has_role_in_guild, is_bot_in_guild
from commands.pool import pool_commands
from commands.register import RegisterCog
from custom_nats import custom_nats
from data.identity import identity_manager
from data.users import user_data
from discord import Intents
from discord.ext import commands
from discord_components import DiscordComponents
from dotenv import load_dotenv
from poll.pollmanager import PollCog
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

async def main():
    # Read from .env
    load_dotenv()

    # nc = asyncio.run(custom_nats.Nats().connect())
    nc = await custom_nats.Nats().connect()

    if nc is None:
        logging.error('Failed to connect to nats server')
        return

    # Creating folder for files
    if not os.path.isdir("data_files"):
        os.mkdir("data_files")

    token = os.environ.get("BOT_ACCESS_TOKEN")
    # loop = asyncio.get_running_loop()


    # Loading user data and identities
    await asyncio.gather(
        user_data.load_from_file(), identity_manager.load_from_file())

    poll_bot.add_check(is_bot_in_guild)
    poll_bot.add_check(has_role_in_guild)

    try:
        # Running pool of commands
        pool_commands.start()

        # Running the bot
        task = asyncio.create_task(poll_bot.start(
            token, bot=True, reconnect=True))
        del token
        await asyncio.wait({task})
    except KeyboardInterrupt:
        print("Waiting for the tasks in the pool to be completed")
        await pool_commands.stop()
        await identity_manager.stop()
        await poll_bot.close()
        await nc.drain()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
