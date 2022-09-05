import logging
import os
from typing import Optional
from nats.aio.client import Client


class Nats():
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            from dotenv import load_dotenv

            try:
                load_dotenv()
            except Exception as e:
                logging.error(e)

            nats_host = os.getenv("NATS_HOST", 'localhost')
            nats_port = os.getenv("NATS_PORT", '4222')

            cls.__instance = super(Nats, cls).__new__(cls)

            cls.__nc: Optional[Client] = None
            cls.__host = nats_host
            cls.__port = nats_port

        return cls.__instance

    @property
    def is_connected(self):
        return self.__nc and self.__nc.is_connected

    @property
    def is_closed(self):
        return self.__nc is None or self.__nc.is_closed

    async def connect(self):
        import nats
        from nats import errors
        from asyncio import TimeoutError

        if self.is_connected:
            return self.__nc

        try:
            self.__nc = await nats.connect(f'{self.__host}:{self.__port}')
        except (OSError, errors.Error, TimeoutError, errors.NoServersError) as e:
            logging.error(e)
            return None

        return self.__nc

    async def close(self):
        if self.is_closed:
            return

        await self.__nc.close()
        self.__nc = None

    async def drain(self):
        if self.is_closed:
            return

        await self.__nc.drain()
        self.__nc = None