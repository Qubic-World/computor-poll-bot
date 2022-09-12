import asyncio
import logging
import os
from typing import Optional
from nats.aio.client import Client
import nats.errors


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
    def nc(self):
        return self.__nc

    @property
    def is_connected(self):
        return self.nc is not None and self.nc.is_connected

    @property
    def is_closed(self):
        return self.nc is None or self.nc.is_closed

    @property
    def is_disconected(self):
        return self.nc is None or self.nc.is_closed or self.nc.is_draining or self.nc.is_draining_pubs

    @property
    def is_connecting(self):
        return self.nc is not None and self.__nc.is_connecting

    @property
    def is_reconnecting(self):
        return self.nc is not None and self.__nc.is_reconnecting

    @property
    def max_payload(self):
        return self.nc.max_payload

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
        if self.is_disconected:
            return

        await self.__nc.close()
        self.__nc = None

    async def drain(self):
        if self.is_disconected:
            return

        await self.__nc.drain()
        self.__nc = None

    async def subscribe(self, subject: str):
        if self.is_disconected:
            return None

        try:
            return await self.nc.subscribe(subject=subject)
        except asyncio.CancelledError as e:
            raise e
        except nats.errors.Error as e:
            logging.exception(e)
            return None

    async def publish(self, subject: str, payload: bytes):
        if self.is_disconected:
            return None

        try:
            return await self.nc.publish(subject=subject, payload=payload)
        except asyncio.CancelledError as e:
            raise e
        except nats.errors.Error as e:
            logging.exception(e)
            return None

        