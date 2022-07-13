import asyncio
import json
import logging

import aiofiles

USER_DATA_FIELD = "user_data"


class UserData():
    def __init__(self) -> None:
        self._user_data = dict()
        self.reset()
        self._json_file_name = "./data_files/userdata.json"
        self._new_identities_callbacks = set()
        self.__removed_identities_callback = set()
        self.background_task = set()

    def __get_user_data(self, user_id: int):
        # The user_id needs to be converted to string. After loading data from a file, the json key is converted from int to string
        user_id_str = str(user_id)
        return next(
            (item for item in self._user_data[USER_DATA_FIELD] if user_id_str in item.keys()), None)

    def _get_user_data(self, user_id: int):
        return self.__get_user_data(user_id)

    def add_data(self, user_id: int, identity_list: list):
        # The user_id needs to be converted to string. After loading data from a file, the json key is converted from int to string
        user_id_str = str(user_id)
        found_data = self.__get_user_data(user_id)
        if found_data == None:
            self._user_data[USER_DATA_FIELD].append(
                {user_id_str: identity_list})
            self.call_new_identities(set(identity_list))
            return (True, "User added")
        else:
            list_data = found_data[user_id_str]
            new_identities = []
            for id in identity_list:
                if not id in list_data:
                    new_identities.append(id)

            if len(new_identities) > 0:
                found_data[user_id_str] = list(set(list_data + new_identities))
                self.call_new_identities(set(new_identities))
                return (True, "User added")

        return (False, "The user is already associated with this ID")

    async def delete_identities(self, user_id: int, identities_for_remove: set):
        data: dict = self.__get_user_data(user_id)
        if data == None:
            logging.warning(
                f"UserData.delete_identities: user with id {user_id} is not found")
            return (False, "User is not found")

        user_identities = set(data[str(user_id)])
        unfound: set = identities_for_remove - user_identities
        will_deleted: set = identities_for_remove - unfound
        if len(will_deleted) > 0:
            data.update({str(user_id): list(user_identities - will_deleted)})
            await self.save_to_file()

            await self.__call_removed_identities(user_id, will_deleted)
            return (True, "ID successfully deleted")

        return (False, "This ID is not registered")

    def get_user_id(self, identity: str) -> int:
        for user_data in self._user_data[USER_DATA_FIELD]:
            if identity in next(iter(user_data.values())):
                return int(next(iter(user_data.keys())))

        return None

    def reset(self):
        self._user_data.clear()
        self._user_data = {USER_DATA_FIELD: []}

    async def save_to_file(self):
        async with aiofiles.open(self._json_file_name, "w") as file:
            await file.write(json.dumps(self._user_data, indent=4))

    async def load_from_file(self):
        try:
            async with aiofiles.open(self._json_file_name, "r") as file:
                self._user_data = json.loads(await file.read())
        except FileNotFoundError:
            self.reset()

    def add_new_identities_callback(self, function):
        self._new_identities_callbacks.add(function)

    def add_removed_identities_callback(self, function):
        self.__removed_identities_callback.add(function)

    async def __call_callback(self, callback, *args):
        if asyncio.iscoroutinefunction(callback):
            await callback(*args)
        else:
            callback(*args)

    def call_new_identities(self, identities: set):
        loop = asyncio.get_event_loop()
        for callback in self._new_identities_callbacks:
            if asyncio.iscoroutinefunction(callback):
                task = loop.create_task(callback(identities))
                self.background_task.add(task)
                task.add_done_callback(self.background_task.discard)
            else:
                callback(identities)

    async def __call_removed_identities(self, user_id: int, identities: set):
        for callback in self.__removed_identities_callback:
            await self.__call_callback(callback, user_id, identities)

    def get_user_identities(self, user_id: int) -> set:
        try:
            user_data = self.__get_user_data(user_id)
            return set(user_data[str(user_id)])
        except:
            return set()

    def is_identity_exist(self, identity: str) -> int:
        for user_data in self._user_data[USER_DATA_FIELD]:
            if identity in list(user_data.values())[0]:
                return int(list(user_data.keys())[0])

        return None


user_data = UserData()
