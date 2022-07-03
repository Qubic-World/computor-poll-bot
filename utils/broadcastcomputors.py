import asyncio
from codecs import StreamReader, StreamWriter
import json
import logging
from typing import Optional

from data.identity import IdentityManager


class BroadcastComputors():
    def __init__(self, identity_manager: IdentityManager, ip: str, port: int, timeout: int = 5) -> None:
        self.identity_manager = identity_manager
        self._ip: str = ip
        self._port: int = port
        self._timeout: int = timeout
        self._reader: Optional[StreamReader] = None
        self._writer: Optional[StreamWriter] = None
        self._connection_task: Optional[asyncio.Task] = None

    async def loop_read(self):
        while True:
            # read size
            raw_data = await self._reader.read(-1)
            # check connect
            if len(raw_data) <= 0:
                return

            try:
                json_obj = json.loads(raw_data.decode())
                identity_set = set(json_obj['identity'])
                self.identity_manager.apply_identity(identity_set)
                await self.identity_manager.save_to_file()
            finally:
                pass

    async def start(self):
        print("Start")
        self._connection_task = asyncio.create_task(
            asyncio.open_connection(self._ip, self._port))
        reader, writer = await asyncio.wait_for(self._connection_task, timeout=self._timeout)
        self._reader = reader
        self._writer = writer
        self._connection_task = None

        if not writer.is_closing():
            await self.loop_read()

    async def stop(self):
        print("Stop")
        if self._connection_task != None:
            self._connection_task.cancel()
            # try:
            #     await self._connection_task
            # except asyncio.CancelledError:
            #     pass

        if self._writer != None and not self._writer.is_closing():
            print("Writer close")
            self._writer.close()
            # await self._writer.wait_closed()


async def broadcast_loop(identity_manager: IdentityManager):
    while True:
        try:
            broadcast = BroadcastComputors(
                identity_manager, "192.168.100.103", 21848, 10)
            await broadcast.start()
        except asyncio.TimeoutError as e:
            logging.warning("broadcast_loop: Timeout")
        except Exception as e:
            print(e)
        finally:
            await broadcast.stop()
