
from asyncio import Queue, Task, create_task
from inspect import iscoroutinefunction
from typing import Optional


class PoolCommands():
    def __init__(self) -> None:
        self.pool = Queue()
        self.task: Optional[Task] = None

    async def add_command(self, func, *args, **kwargs):
        if self.pool.full():
            await self.pool.put((func, args, kwargs))
        else:
            self.pool.put_nowait((func, args, kwargs))

    async def _execute(self):
        while True:
            try:
                func_tuple = await self.pool.get()
                func = func_tuple[0]
                args = func_tuple[1]
                kwargs = func_tuple[2]
                if iscoroutinefunction(func):
                    await func(*args, **kwargs)
                else:
                    func(*args, **kwargs)
            finally:
                self.pool.task_done()

    def __len__(self):
        return self.pool.qsize()

    def start(self):
        self.task = create_task(self.execute())

    async def stop(self):
        if len(self) > 0:
            await self.pool.join()

        self.task.cancel()