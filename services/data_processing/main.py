import asyncio
import logging
from ctypes import sizeof
from itertools import groupby

from algorithms.verify import get_score
from custom_nats.custom_nats import Nats
from custom_nats.handler import Handler, HandlerStarter
from nats.aio.msg import Msg
from qubic.qubicdata import (NUMBER_OF_SOLUTION_NONCES,
                             BroadcastResourceTestingSolution,
                             ResourceTestingSolution, Subjects, Tick)
from qubic.qubicutils import get_identity


class HandleBroadcastResourceTestingSolution(Handler):
    async def get_sub(self):
        if self._nc.is_disconected:
            return None

        return await self._nc.subscribe(Subjects.BROADCAST_RESOURCE_TESTING_SOLUTION)

    async def _handler_msg(self, msg):
        if msg is None:
            return None

        data = msg.data

        if len(data) != sizeof(BroadcastResourceTestingSolution):
            self._warning(
                'BroadcastResourceTestingSolution structure size does not match payload size')
            return None

        broadcastResourceTestingSolution = BroadcastResourceTestingSolution.from_buffer_copy(
            data)
        resourceTestingSolution: ResourceTestingSolution = broadcastResourceTestingSolution.resourceTestingSolution
        identity = get_identity(
            bytes(resourceTestingSolution.computorPublicKey))
        score = get_score(
            bytes(resourceTestingSolution.nonces), NUMBER_OF_SOLUTION_NONCES)

        logging.info(
            f'BroadcastResourceTestingSolution: {identity} -- {score}')


class HandleBroadcastTick(Handler):
    def __init__(self, nc: Nats) -> None:
        super().__init__(nc)

        self.__ticks = dict()

    async def get_sub(self):
        if self._nc.is_disconected:
            return None

        return await self._nc.subscribe(Subjects.BROADCAST_TICK)

    async def _handler_msg(self, msg: Msg):
        if msg is None:
            return None

        data = msg.data

        if len(data) != sizeof(Tick):
            self._warning(
                'BroadcastResourceTestingSolution structure size does not match payload size')
            return None

        tick_structure = Tick.from_buffer_copy(data)

        saved_tick = self.__ticks.get(tick_structure.computorIndex, 0)
        if saved_tick < tick_structure.tick:
            self.__ticks[tick_structure.computorIndex] = tick_structure.tick

        ticks = sorted(self.__ticks.keys(), reverse=True)

        logging.debug([(k, len(list(g))) for k, g in groupby(ticks)])


async def main():
    logging.info('Start data processig')

    logging.info('Connecting to the nats server')

    nc = Nats()
    await nc.connect()

    logging.info('Subscribing to data')

    tasks = [
        asyncio.create_task(HandlerStarter.start(
            HandleBroadcastResourceTestingSolution(nc))),
        asyncio.create_task(HandlerStarter.start(HandleBroadcastTick(nc)))
    ]

    await asyncio.wait(tasks)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
