import json

import aiofiles

USER_DATA_FIELD = "user_data"


class UserData():
    def __init__(self) -> None:
        self._json_data = dict()
        self.reset()
        self._json_file_name = "userdata.json"

    def add_data(self, user_id: str, identity_list: list):
        found_id = next(
            (item for item in self._json_data[USER_DATA_FIELD] if user_id in item.keys()), False)
        if found_id == False:
            self._json_data[USER_DATA_FIELD].append({user_id: identity_list})
        else:
            list_data = found_id[user_id]
            found_id[user_id] = list(set(list_data + identity_list))

    def get_user_id(self, identity: str):
        for user_data in self._json_data[USER_DATA_FIELD]:
            if identity in next(iter(user_data.values())):
                return next(iter(user_data.keys()))

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
