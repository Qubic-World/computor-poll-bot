import logging
import os
from typing import Optional
from nats.aio.client import Client


class custom_nats():
    __TIMEOUT = 5

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

            cls.__instance = super(custom_nats, cls).__new__(cls)

            cls.__nc = Optional[Client]
            cls.__host = nats_host
            cls.__port = nats_port

        return cls.__instance

    @classmethod
    @property
    def is_connected(cls):
        return cls.__nc and cls.__nc.is_connected

    @classmethod
    @property
    def is_closed(cls):
        return cls.__nc is None or cls.__nc.is_closed

    @classmethod
    async def connect(cls):
        import nats
        from nats import errors
        from asyncio import TimeoutError

        if cls.is_connected:
            return cls.__nc

        try:
            cls.__nc = await nats.connect(f'{cls.__host}:{cls.__port}')
        except (OSError, errors.Error, TimeoutError, errors.NoServersError) as e:
            logging.error(e)
            return None

        return cls.__nc

    @classmethod
    async def close(cls):
        if cls.is_closed:
            return

        await cls.__nc.close()
        cls.__nc = None

    @classmethod
    async def drain(cls):
        if cls.is_closed:
            return

        await cls.__nc.drain()
        cls.__nc = None