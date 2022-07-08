import asyncio
import json

import aiofiles

USER_DATA_FIELD = "user_data"


class UserData():
    def __init__(self) -> None:
        self._json_data = dict()
        self.reset()
        self._json_file_name = "./data_files/userdata.json"
        self._observers_new_identities = set()
        self.background_task = set()

    def __get_user_data(self, user_id: int):
        user_id_str = str(user_id)
        return next(
            (item for item in self._json_data[USER_DATA_FIELD] if user_id_str in item.keys()), None)

    def add_data(self, user_id: int, identity_list: list):
        # The user_id needs to be converted to string. After loading data from a file, the json key is converted from int to string
        user_id_str = str(user_id)
        found_id = next(
            (item for item in self._json_data[USER_DATA_FIELD] if user_id_str in item.keys()), False)
        if found_id == False:
            self._json_data[USER_DATA_FIELD].append(
                {user_id_str: identity_list})
            self.call_new_identities(set(identity_list))
            return (True, "User added")
        else:
            list_data = found_id[user_id_str]
            new_identities = []
            for id in identity_list:
                if not id in list_data:
                    new_identities.append(id)

            if len(new_identities) > 0:
                found_id[user_id_str] = list(set(list_data + new_identities))
                self.call_new_identities(set(new_identities))
                return (True, "User added")

        return (False, "The user is already associated with this ID")

    def get_user_id(self, identity: str) -> int:
        for user_data in self._json_data[USER_DATA_FIELD]:
            if identity in next(iter(user_data.values())):
                return int(next(iter(user_data.keys())))

        return None

    def reset(self):
        self._json_data.clear()
        self._json_data = {USER_DATA_FIELD: []}

    async def save_to_file(self):
        async with aiofiles.open(self._json_file_name, "w") as file:
            await file.write(json.dumps(self._json_data, indent=4))

    async def load_from_file(self):
        try:
            async with aiofiles.open(self._json_file_name, "r") as file:
                self._json_data = json.loads(await file.read())
        except FileNotFoundError:
            self.reset()

    def observe_new_identities(self, function):
        self._observers_new_identities.add(function)

    def call_new_identities(self, identities: set):
        loop = asyncio.get_event_loop()
        for observer in self._observers_new_identities:
            if asyncio.iscoroutinefunction(observer):
                task = loop.create_task(observer(identities))
                self.background_task.add(task)
                task.add_done_callback(self.background_task.discard)
            else:
                observer(identities)

    def user_identity(self, user_id: int) -> set:
        try:
            iter = self.__get_user_data(user_id)
            return set(iter[str(user_id)])
        except:
            return set()


user_data = UserData()
