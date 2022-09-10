import asyncio
import logging
from inspect import iscoroutinefunction, isfunction, ismethod


class Callbacks():
    def __init__(self):
        self.__tasks = set()
        self.__callbacks = set()

    def add_callbacks(self, callbacks: set):
        for callback in callbacks:
            self.add_callback(callback=callback)

    def add_callback(self, callback):
        if isfunction(callback) or ismethod(callback):
            self.__callbacks.add(callback)

    def execute(self, *args, **kwargs):
        for callback in self.__callbacks:
            if iscoroutinefunction(callback):
                task = asyncio.create_task(callback(*args, **kwargs))
                if not task.done():
                    self.__tasks.add(task)
                    task.add_done_callback(self.__tasks.remove)
            else:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logging.exception(e)

    async def stop(self):
        if len(self.__tasks) > 0:
            task: asyncio.Task = None
            for task in self.__tasks:
                task.cancel()

            await asyncio.sleep(0)
