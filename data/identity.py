import asyncio
import aiofiles
import ast
import itertools


class IdentityManager():
    def __init__(self) -> None:
        self._identity = set()
        self._file_name = "./data_files/identity.data"
        self.__added_callback = set()
        self.__removed_callback = set()
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

    @property
    def identity(self) -> set:
        """All identities
        """
        return self._identity
    @property
    def computor_identities(self) -> set:
        """676 identities
        """
        return set(itertools.islice(self._identity, 676))

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

    def add_new_identities_callback(self, function):
        self.__added_callback.add(function)

    def add_removed_identities_callback(self, function):
        self.__removed_callback.add(function)

    def call_removed(self, removed_identity: set):
        loop = asyncio.get_event_loop()
        for observer in self.__removed_callback:
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
        for observer in self.__added_callback:
            if asyncio.iscoroutinefunction(observer):
                task =loop.create_task(observer(added_identity))
                self.background_task.add(task)
                task.add_done_callback(self.background_task.discard)
            else:
                observer(added_identity)

        # TODO: Will it affect other coroutines?
        if not loop.is_running():
            loop.close()

    def on_new_identities(self, identities: set):
        existing_identities = set()
        for id in identities:
            if id in self._identity:
                existing_identities.add(id)
                
        if len(existing_identities) > 0:
            self.call_added_new(existing_identities)

    def get_only_computor_identities(self, identities: set)->set:
        """Takes the identities and returns only those that are computors
        """
        not_computors = identities - self.computor_identities
        return identities - not_computors


identity_manager = IdentityManager()