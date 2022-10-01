import asyncio
import logging
from inspect import iscoroutinefunction


class BackgroundTasks():
    def __init__(self) -> None:
        self._background_tasks = set()

    def create_task(self, f, *args, **kwargs) -> asyncio.Task:
        if not iscoroutinefunction(f):
            logging.exception('The function is not a coroutine')
            return

        task = asyncio.create_task(f(*args, **kwargs))
        self.add_task(task)
        return task

    async def create_and_wait(self, f, *args, **kwargs):
        if not iscoroutinefunction(f):
            logging.exception('The function is not a coroutine')
            return

        task = asyncio.create_task(f(*args, **kwargs))
        self.add_task(task)

        done, pending = await asyncio.wait([task])
        done_task: asyncio.Task = None
        for done_task in done:
            try:
                e = done_task.exception()
            except asyncio.CancelledError():
                e = None

            if e is not None:
                logging.exception(e)

    def add_task(self, task: asyncio.Task):
        try:
            if not task.done():
                self._background_tasks.add(task)
                task.add_done_callback(self._remove_task)
        except Exception as e:
            logging.exception(e)

    def _remove_task(self, task):
        try:
            self._background_tasks.remove(task)
        except Exception as e:
            logging.exception(e)

    async def close(self):
        task: asyncio.Task = None
        for task in self._background_tasks:
            if not task.done():
                task.cancel()

        if len(self._background_tasks) <= 0:
            return

        done, pending = await asyncio.wait(self._background_tasks)

    def __len__(self):
        return len(self._background_tasks)
