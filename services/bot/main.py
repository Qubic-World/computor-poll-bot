import asyncio
import logging
import os
from ctypes import sizeof
from typing import Optional

from custom_nats import custom_nats
from custom_nats.handler import Handler, HandlerStarter
from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv
from nats.aio.client import Client
from qubic.qubicdata import BroadcastComputors, Computors, Subjects
from qubic.qubicutils import (cache_computors, get_comutors_system_data,
                              get_identities_from_computors)

from checkers import has_role_in_guild, is_bot_in_guild
from commands.pool import pool_commands
from commands.register import RegisterCog
from data.identity import identity_manager
from data.users import user_data
from poll.pollmanager import PollCog
from role import RoleManager

"""Commands Bot
"""
intents = Intents.default()
intents.members = True
intents.messages = True
poll_bot = commands.Bot(command_prefix="/", intents=intents)

"""Managers
"""
role_manager = RoleManager(user_data, poll_bot)

"""Nats
"""

__nc: Optional[Client] = None


class HandlerWaitBroadcastComputors(Handler):
    def __init__(self, nc) -> None:
        super().__init__(nc)

    async def get_sub(self):
        return await self._nc.nc.subscribe(Subjects.BROADCAST_COMPUTORS)

    async def _handler_msg(self, msg):
        from qubic.qubicutils import get_identities_from_computors
        if msg is None or msg.data is None:
            return

        data = msg.data
        if len(data) != sizeof(BroadcastComputors):
            logging.warning(
                f'{HandlerWaitBroadcastComputors.__name__}: the size of the data does not match the size of the {BroadcastComputors.__name__} structure')
            return

        computors: Computors = BroadcastComputors.from_buffer_copy(
            data).computors
        await cache_computors(computors)
        identities = get_identities_from_computors(computors=computors)
        identity_manager.apply_identity(identities)
        await identity_manager.save_to_file()


"""Commands
"""


@poll_bot.event
async def on_ready():
    print("On ready")

    poll_cog = PollCog(poll_bot)
    register_cog = RegisterCog(poll_bot)
    await asyncio.wait({
        asyncio.create_task(poll_cog._load_polls_from_file())
    })
    await poll_bot.add_cog(poll_cog)
    await poll_bot.add_cog(register_cog)

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

    # Loading identity from Computors
    identity_manager.apply_identity(
        get_identities_from_computors(get_comutors_system_data()))
    await identity_manager.save_to_file()

    # After starting the bot, reassign the roles
    await role_manager.reassign_roles()


def main():
    # Read from .env
    load_dotenv()

    loop = asyncio.get_event_loop()

    global __nc
    __nc = loop.run_until_complete(custom_nats.Nats().connect())

    if __nc is None:
        logging.error('Failed to connect to nats server')
        return

    # Creating folder for files
    if not os.path.isdir(os.getenv('DATA_FILES_PATH', './')):
        os.mkdir(os.getenv('DATA_FILES_PATH', './'))

    token = os.environ.get("BOT_ACCESS_TOKEN")

    # Loading user data and identities
    loop.run_until_complete(asyncio.wait({
        loop.create_task(user_data.load_from_file()),
        loop.create_task(identity_manager.load_from_file())}))

    poll_bot.add_check(is_bot_in_guild)
    poll_bot.add_check(has_role_in_guild)

    try:
        # Running pool of commands
        pool_commands.start()

        # Running the bot
        tasks = {
            loop.create_task(poll_bot.start(token, reconnect=True)),
            loop.create_task(HandlerStarter.start(
                HandlerWaitBroadcastComputors(nc=custom_nats.Nats())))
        }
        loop.run_until_complete(asyncio.wait(tasks))
    except KeyboardInterrupt:
        print("Waiting for the tasks in the pool to be completed")
        loop.run_until_complete(pool_commands.stop())
        loop.run_until_complete(identity_manager.stop())
        loop.run_until_complete(poll_bot.close())
        loop.run_until_complete(__nc.drain())
    finally:
        if not loop.is_closed():
            loop.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
