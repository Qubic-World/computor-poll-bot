import asyncio
import logging
from typing import Optional

from nats.aio.msg import Msg
from nats.aio.subscription import Subscription

from custom_nats.custom_nats import Nats


class Handler():
    def __init__(self, nc: Nats) -> None:
        self._nc = nc
        self._sub: Optional[Subscription] = None
        self._background_tasks = set()

    def add_task(self, task: asyncio.Task):
        try:
            if not task.done():
                self._background_tasks.add(task)
                task.add_done_callback(self.remove_task)
        except Exception as e:
            logging.exception(e)

    def remove_task(self, task):
        try:
            self._background_tasks.remove(task)
        except Exception as e:
            logging.exception(e)

    @classmethod
    def __log(cls, level: int, msg: str):
        logging.log(level=level, msg=(f'{cls.__name__}: ' + msg))

    @classmethod
    def _warning(cls, msg: str):
        cls.__log(logging.WARNING, msg)

    @classmethod
    def _error(cls, msg: str):
        cls.__log(logging.ERROR, msg)

    @classmethod
    def _info(cls, msg: str):
        cls.__log(logging.INFO, msg)

    @classmethod
    def _debug(cls, msg: str):
        cls.__log(logging.DEBUG, msg)

    async def loop(self):
        sub = await self.get_sub()
        if sub is None:
            return

        if not isinstance(sub, Subscription):
            logging.exception(TypeError(f'Subscription must be of the {Subscription.__name__} type'))

        self._sub = sub
        try:
            while not sub._closed and not self._nc.is_disconected:
                msg = await self._wait_msg(sub)
                if msg is None:
                    continue

                await self._handler_msg(msg)
        except Exception as e:
            logging.exception(e)

    async def cancel(self):
        task: asyncio.Task = None
        for task in self._background_tasks:
            task.cancel()

        task = asyncio.create_task(asyncio.sleep(0))

        if self._sub is not None and not self._sub._closed:
            await self._sub.unsubscribe()

        if not task.done():
            await asyncio.wait({task})

    async def get_sub(self) -> Subscription | None:
        return None

    async def _wait_msg(self, sub: Subscription) -> Msg | None:
        from asyncio import TimeoutError

        if sub == None or sub._closed:
            return None

        try:
            self._debug('waiting a message')
            msg = await sub.next_msg()
            self._debug('message received')
        except TimeoutError as e:
            return None

        return msg

    async def _handler_msg(self, msg: Msg):
        pass


class HandlerWrapper():
    def __init__(self, handler: Handler) -> None:
        assert isinstance(
            handler, Handler), f"{HandlerWrapper.__name__} should only work with the {Handler.__name__} class"
        self.__handler = handler

    async def __aenter__(self):
        logging.debug(f'{HandlerWrapper.__name__}: __aenter__')
        return self.__handler

    async def __aexit__(self, *exc_info):
        logging.debug(f'{HandlerWrapper.__name__}: __aexit__')
        await self.__handler.cancel()


class HandlerStarter():
    @staticmethod
    async def start(handler: Handler):
        assert isinstance(
            handler, Handler), f"{HandlerStarter.__name__} should only work with the {Handler.__name__} class"
        async with HandlerWrapper(handler) as h:
            await h.loop()
