import asyncio
import aiofiles
import ast


class IdentityManager():
    def __init__(self) -> None:
        self._identity = set()
        self._file_name = "identity.data"
        self._observers_added = set()
        self._observers_removed = set()
        self.background_task = set()

    def apply_identity(self, identity: set):
        old_identity = self._identity.difference(identity)
        new_identity = identity.difference(self._identity)

        self._identity = identity

        if len(new_identity) > 0:
            self.call_added_new(new_identity)
        if len(old_identity) > 0:
            self.call_removed(old_identity)

    def reset(self):
        self._identity.clear()

    async def stop(self):
        while len(self.background_task) > 0:
            asyncio.sleep(0.1)

    """
    Files
    """

    async def save_to_file(self):
        async with aiofiles.open(self._file_name, "w") as file:
            await file.write(str(self._identity))

    async def load_from_file(self):
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
        loop = asyncio.get_event_loop()
        for observer in self._observers_removed:
            if asyncio.iscoroutinefunction(observer):
                task = loop.create_task(observer(removed_identity))
                self.background_task.add(task)
                task.add_done_callback(self.background_task.discard)
            else:
                observer(removed_identity)
        if not loop.is_running():
            loop.close()

    def call_added_new(self, added_identity: set):
        loop = asyncio.get_event_loop()
        for observer in self._observers_added:
            if asyncio.iscoroutinefunction(observer):
                task =loop.create_task(observer(added_identity))
                self.background_task.add(task)
                task.add_done_callback(self.background_task.discard)
            else:
                observer(added_identity)

        # TODO: Will it affect other coroutines?
        if not loop.is_running():
            loop.close()

identity_manager = IdentityManager()