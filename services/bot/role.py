import asyncio
import logging
import traceback

import discord.utils
from discord import Client, Member, Role

from data.identity import identity_manager
from data.users import UserData, user_data
from utils.botutils import get_member_by_id, get_role
from utils.message import is_valid_identity


class RoleManager():
    def __init__(self, user_data: UserData, bot: Client) -> None:
        self._user_data: UserData = user_data
        self._bot: Client = bot

    async def __set_role_to_member(self, member: Member, set_role: bool = True):
        if member == None:
            traceback.print_stack()
            logging.warning("RoleManager.__set_role_to_membet: member is None")
            return

        if member.bot:
            raise ValueError("you cannot assign a role to the bot")

        try:
            role: Role = get_role(self._bot)
            if set_role:
                if discord.utils.get(member.roles, id=role.id) == None:
                    await member.add_roles(role)
            else:
                if discord.utils.get(member.roles, id=role.id) != None:
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
            """If the user has other IDs that are computors, we do not remove the role
            """
            if set_role == False:
                user_identity_set = user_data.get_user_identities(user_id)
                for user_identity in user_identity_set:
                    if user_identity in identity_manager.computor_identities:
                        continue

            if user_id != None:
                member = get_member_by_id(self._bot, user_id)
                if member != None:
                    await self.__set_role_to_member(member, set_role)

    async def reassign_roles(self, *args):
        """Reassigning the role if the status of the ID computor has changed
        """
        user_id_list = user_data.get_all_users()
        # (member, set_role: bool)
        members = []
        for user_id in user_id_list:
            member: Member = get_member_by_id(self._bot, user_id)
            if member == None:
                logging.warning(
                    "RoleManager.reset_roles: failed to get a member")
                continue

            if len(identity_manager.get_only_computor_identities(user_data.get_user_identities(user_id))) <= 0:
                members.append((member, False))
            else:
                members.append((member, True))

        tasks = []
        for member in members:
            tasks.append(asyncio.create_task(
                self.__set_role_to_member(member[0], member[1])))

        await asyncio.wait(tasks)

    async def reassing_role(self, user_id: int, *args):
        """Reassigning the role if the status of the ID computor has changed
        """
        member: Member = get_member_by_id(self._bot, user_id)
        if member == None:
            logging.warning(
                "RoleManager.reset_roles: failed to get a member")
            return

        has_computors = len(identity_manager.get_only_computor_identities(user_data.get_user_identities(user_id))) > 0
        await self.__set_role_to_member(member, has_computors)

