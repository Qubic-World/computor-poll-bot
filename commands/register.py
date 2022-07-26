import asyncio
import os

from checkers import is_user_in_guild
from data.identity import identity_manager
from data.users import user_data
from discord import Client, DMChannel, Embed
from discord.ext import commands
from discord.ext.commands import Context
from utils.botutils import get_username_with_discr
from utils.message import (get_identity_list, get_username_from_message,
                           is_valid_message)
from verify.user import get_member_by_username, get_user_id_from_username

from commands.pool import pool_commands


class RegisterCog(commands.Cog):
    def __init__(self, bot: Client) -> None:
        super().__init__()
        self.__bot = bot

    @commands.command(aliases=["reg_stats"])
    @commands.check(is_user_in_guild)
    async def reg_data(self, ctx: Context):
        """Prints the number of registered users and IDs
        """
        await pool_commands.add_command(self.__reg_data, ctx)

    async def __reg_data(self, ctx: Context):
        users = len(user_data.get_all_users())
        identities = len(user_data.get_all_identities())
        description = f"Users: {users}{os.linesep}IDs: {identities}"
        e = Embed(title="Total registered",
                  description=description)

        is_dm = isinstance(ctx.channel, DMChannel)
        delete_after = None if is_dm else 10

        if is_dm:
            user_identities = user_data.get_user_identities(ctx.author.id)
            all_len = len(user_identities)
            only_comp_len = len(identity_manager.get_only_computor_identities(
                user_identities))

            e.add_field(name="Your IDs are registered:\nTotal ID",
                        value=all_len)
            e.add_field(name=u"\u200b\nAre computors", value=only_comp_len)

        await ctx.reply(embed=e, delete_after=delete_after)

    @commands.command(name='register')
    @commands.check(is_user_in_guild)
    async def register(self, ctx, *, json):
        """User registration
        Example:
        /register {
            "identity": "BPFJANADOGBDLNNONDILEMAICAKMEEGBFPJBKPBCEDFJIALDONODMAIMDBFKCFEEMEOLFK",
            "message": "For ComputorPollBot from N-010#3073",
            "signature": "bhijbaejihfcgpbmoddoihhfhoapmdhnogkolnimfekndhpdddeddjfhopmdbacbjjcjcddmklmdkfeplkbdaiogdboobiiodmhndphmoaljnaeedcoaijnfpddebdaadg"
        }
        """
        # Adding to the pool
        await pool_commands.add_command(self.__register, ctx, json, False)

    # Executing from pool
    async def __register(self, ctx: commands.Context, json, unregister: bool = False):
        """User registration
        """

        # DM only
        if not isinstance(ctx.channel, DMChannel):
            await ctx.reply(f"{'Registration' if unregister == False else 'Deregistration'} is only available through the bot's private messages", delete_after=10)
            return

        result = is_valid_message(json)
        if result[0] == False:
            await ctx.reply(result[1])
            return

        username = get_username_from_message(json)
        if len(username) <= 0:
            await ctx.reply("Failed to retrieve username from message field")
            return

        member = get_member_by_username(self.__bot, username)
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
            user_id = get_user_id_from_username(self.__bot, username)
            if user_id == None:
                message = str("Unable to find the user")
        except ValueError as e:
            message = str("Error: " + str(e))
        finally:
            if len(message) > 0:
                await ctx.reply(message)
                return

        if unregister == False:
            identity_list = get_identity_list(json)
            found_user_id = user_data.is_identity_exist(identity_list[0])
            if found_user_id == None:
                result = await user_data.add_data(user_id, identity_list)
            else:
                result = (False, "This ID is already registered")
        else:
            result = await user_data.delete_identities(user_id, set(get_identity_list(json)))

        if result[0] == False:
            await ctx.reply(result[1])
            return

        await asyncio.gather(user_data.save_to_file(), ctx.reply(result[1]))

    @commands.command(aliases=["deregister"])
    @commands.check(is_user_in_guild)
    async def unregister(self, ctx, *, json):
        """Unregister ID
        /unregister {
            "identity": "BPFJANADOGBDLNNONDILEMAICAKMEEGBFPJBKPBCEDFJIALDONODMAIMDBFKCFEEMEOLFK",
            "message": "For ComputorPollBot from N-010#3073",
            "signature": "bhijbaejihfcgpbmoddoihhfhoapmdhnogkolnimfekndhpdddeddjfhopmdbacbjjcjcddmklmdkfeplkbdaiogdboobiiodmhndphmoaljnaeedcoaijnfpddebdaadg"
        }
        """
        await pool_commands.add_command(self.__register, ctx, json, True)

    @commands.command()
    @commands.check(is_user_in_guild)
    async def index(self, ctx, id: str):
        """
        Displays the ID index. The first index is 0

        Example:
        /index BPFJANADOGBDLNNONDILEMAICAKMEEGBFPJBKPBCEDFJIALDONODMAIMDBFKCFEEMEOLFK
        """
        await pool_commands.add_command(self.__index, ctx, id)

    async def __index(self, ctx: Context, id: str):
        try:
            index = identity_manager.identity.index(id)
            if index < 676:
                h = chr(int(index / 26) + 65)
                l = chr((index % 26) + 65)
                message = f"Your index: {h+l}"
            else:
                message = "Your ID is not a computor"
        except ValueError:
            index = None
            message = "You id was not found"

        await ctx.reply(message)
