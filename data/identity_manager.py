import aiofiles
import ast


class IdentityManager():
    def __init__(self) -> None:
        self._identity = set()
        self._file_name = "identity.data"
        self._observers_added = set()
        self._observers_removed = set()

    def apply_identity(self, identity: set):
        old_identity = self._identity.difference(identity)
        new_identity = identity.difference(self._identity)

        self._identity = identity

        self.call_added_new(new_identity)
        self.call_removed(old_identity)

    def reset(self):
        self._identity.clear()

    """
    Files
    """

    async def save_to_file(self):
        async with aiofiles.open(self._file_name, "w") as file:
            await file.write(str(self._identity))

    async def read_from_file(self):
        try:
            async with aiofiles.open(self._file_name, "r") as file:
                self._identity = set(ast.literal_eval(await file.read()))
        except:
            pass

    """
    Decorators
    """

    def observe_added(self, function):
        self._observers_added.add(function)

    def observe_removed(self, function):
        self._observers_removed.add(function)

    def call_removed(self, removed_identity: set):
        for observer in self._observers_removed:
            observer(removed_identity)

    def call_added_new(self, added_identity: set):
        for observer in self._observers_added:
            observer(added_identity)
