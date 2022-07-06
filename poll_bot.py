import asyncio
import os

from discord import Intents, Member
from discord.ext import commands
from dotenv import load_dotenv
from checkers import is_valid_channel, is_valid_role

from commands.pool import PoolCommands
from qubic.manager import QubicNetworkManager
from qubic.qubicutils import load_cache_computors
from role import RoleManager
from data.identity import identity_manager
from data.users import UserData
from utils.botutils import get_guild, get_role
from utils.message import (get_identity_list, get_username_from_message,
                           is_valid_message)
from verify.user import get_user_id_from_username

intents = Intents.default()
intents.members = True
intents.messages = True
poll_bot = commands.Bot(command_prefix="/", intents=intents)

pool_commands = PoolCommands()
user_data = UserData()
role_manager = RoleManager(user_data, poll_bot)


@poll_bot.command(name='register')
@commands.check(is_valid_channel)
@commands.check(is_valid_role)
# Adding to the pool
async def _register(ctx, *, json):
    await pool_commands.add_command(register, ctx, json)

# Executing from pool
async def register(ctx: commands.Context, json):
    result = is_valid_message(json)
    if result[0] == False:
        await ctx.reply(result[1])
        return

    username = get_username_from_message(json)
    if len(username) <= 0:
        await ctx.reply("Failed to retrieve username from message field")
        return

    try:
        message = ""
        user_id = get_user_id_from_username(poll_bot, username)
        if user_id == None:
            message = "Unable to find the user"
    except ValueError as e:
        message = str(e)
    finally:
        if len(message) > 0:
            await ctx.reply(message)
            return

    result = user_data.add_data(user_id, get_identity_list(json))
    if result[0] == False:
        await ctx.reply(result[1])
        return

    await asyncio.gather(user_data.save_to_file(), ctx.reply(f"User {username} added"))


@poll_bot.command(name="roles")
@commands.check(is_valid_channel)
async def _roles(ctx):
    await pool_commands.add_command(roles, ctx)


async def roles(ctx: commands.Context):
    guild = get_guild(poll_bot)

    member: Member = ctx.message.author
    await ctx.reply(member.guild.name)
    try:
        await member.add_roles(get_role(poll_bot))
    except Exception as e:
        ctx.reply(str(e))


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
    user_data.observe_new_identities(identity_manager.on_new_identities)

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

        # TODO:
        # network_task = loop.create_task(network.start())
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
        # if not network_task.cancelled():
        #     network_task.cancel()
        # try:
        #     loop.run_until_complete(network_task)
        # except asyncio.CancelledError:
        #     pass
    finally:
        if not loop.is_closed():
            loop.close()


if __name__ == "__main__":
    main()
