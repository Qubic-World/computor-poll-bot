import logging

from discord import Client, Guild, Member

from data.users import UserData
from utils.botutils import (get_channel, get_channel_id, get_member_by_id,
                            get_role)
from verify.message import is_valid_identity


class RoleManager():
    def __init__(self, user_data: UserData, bot: Client) -> None:
        self._user_data: UserData = user_data
        self._bot: Client = bot

    async def __set_role_to_member(self, guild: Guild, member: Member, set_role: bool = True):
        if member.bot:
            raise ValueError("you cannot assign a role to the bot")

        try:
            role = get_role(guild)
            if set_role:
                await member.add_roles(role)
            else:
                await member.remove_roles(role)
        finally:
            pass

    async def __set_role(self, identity: set, set_role: bool = True):
        if len(identity) < 0:
            raise ValueError("identity cannot be empty")

        valid_identity: set = [
            item for item in identity if is_valid_identity(item)]
        for id in valid_identity:
            user_id = self._user_data.get_user_id(id)
            if user_id != None:
                member = get_member_by_id(self._bot, user_id)
                if member != None:
                    channel = get_channel(self._bot)
                    if channel != None:
                        await self.__set_role_to_member(channel.guild, member, set_role)
                    else:
                        raise ValueError(
                            f"Failed to get a channel by ID: {get_channel_id()}")

    async def add_role(self, identity: set):
        try:
            await self.__set_role(identity, True)
        except Exception as e:
            logging.error(e)

    async def remove_role(self, identity: set):
        try:
            await self.__set_role(identity, False)
        except Exception as e:
            logging.error(e)
