
import asyncio
import logging
from asyncio import Queue, Task
from inspect import iscoroutinefunction
from typing import Optional


class PoolCommands():
    def __init__(self) -> None:
        self.pool = Queue()
        self._task: Optional[Task] = None

    async def add_command(self, func, *args, **kwargs):

        if self.pool.full():
            await self.pool.put((func, args, kwargs))
        else:
            self.pool.put_nowait((func, args, kwargs))

    async def execute(self):
        while True:
            try:
                func_tuple = await self.pool.get()
                func = func_tuple[0]
                args = func_tuple[1]
                kwargs = func_tuple[2]

                if iscoroutinefunction(func):
                    try:
                        await asyncio.wait_for(func(*args, **kwargs), 5)
                    except asyncio.TimeoutError as e:
                        logging.warning('PoolCommands.execute: timeout')
                else:
                    func(*args, **kwargs)

            except Exception as e:
                logging.error(e)

            try:
                self.pool.task_done()
            except ValueError:
                pass

    def __len__(self):
        return self.pool.qsize()

    def start(self):
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self.execute())

    async def stop(self):
        await self.pool.join()

        if self._task != None:
            self._task.cancel()


pool_commands = PoolCommands()
