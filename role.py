import logging

from discord import Client, Member

from data.identity import identity_manager
from data.users import UserData, user_data
from utils.botutils import get_member_by_id, get_role
from utils.message import is_valid_identity


class RoleManager():
    def __init__(self, user_data: UserData, bot: Client) -> None:
        self._user_data: UserData = user_data
        self._bot: Client = bot

    async def __set_role_to_member(self, member: Member, set_role: bool = True):
        if member.bot:
            raise ValueError("you cannot assign a role to the bot")

        try:
            role = get_role(self._bot)
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

    async def add_role(self, identities: set):
        try:
            computor_identities = set([id for id in identities if id in identity_manager.computor_identities])
            if len(computor_identities) > 0:
                print(list(identity_manager.computor_identities).index(list(computor_identities)[0]))
                await self.__set_role(computor_identities, True)
        except Exception as e:
            logging.error(e)

    async def remove_role(self, identities: set):
        try:
            await self.__set_role(identities, False)
        except Exception as e:
            logging.error(e)

    async def removed_identities_from_user(self, user_id: int, identities: set):
        """
        When a user has deleted their IDs. 
        Check if the remaining ones are Computors. If not, delete the role
        """

        user_identities = user_data.get_user_identities(user_id)
        member = get_member_by_id(self._bot, user_id)
        if member == None:
            logging.warning(
                f"RoleManager.removed_identities_from_user: \
                failed to get the member user with id {user_id} ")
            return

        for user_id in user_identities:
            if user_id in identity_manager.computor_identities:
                return

        await self.__set_role_to_member(member, False)
