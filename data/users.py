import json

import aiofiles


class UserData():
    def __init__(self) -> None:
        self._json_data = dict({"user_data": []})
        self._json_data.setdefault("user_data", [])
        self._json_file_name = "userdata.json"

    def add_data(self, user_id: str, identity_list: list):
        found_id = next(
            (item for item in self._json_data['user_data'] if user_id in item.keys()), False)
        if found_id == False:
            self._json_data['user_data'].append({user_id: identity_list})
        else:
            list_data = found_id[user_id]
            found_id[user_id] = list(set(list_data + identity_list))

    def reset(self):
        self._json_data.clear()
        self._json_data = {"user_data": []}

    async def save_to_file(self):
        async with aiofiles.open(self._json_file_name, "w") as file:
            await file.write(json.dumps(self._json_data, indent=4))

    async def load_from_file(self):
        try:
            async with aiofiles.open(self._json_file_name, "r") as file:
                self._json_data = json.loads(await file.read())
        except FileNotFoundError:
            self.reset()
