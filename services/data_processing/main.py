import asyncio
import logging
from ctypes import sizeof
from typing import Optional

from algorithms.verify import get_score
from custom_nats.custom_nats import Nats
from custom_nats.handler import Handler, HandlerStarter
from nats.aio.msg import Msg
from qubic.qubicdata import (NUMBER_OF_SOLUTION_NONCES, BroadcastComputors,
                             BroadcastResourceTestingSolution, Computors,
                             ResourceTestingSolution, Subjects, Tick)
from qubic.qubicutils import get_identity


class HandleBroadcastComputors(Handler):
    def __init__(self, nc: Nats) -> None:
        super().__init__(nc)

        self.__computors: Optional[Computors] = None
        self.add_task(asyncio.create_task(self.print_computors()))

    async def print_computors(self):
        while True:
            logging.info('Computors:')
            if self.__computors is not None:
                logging.info(f'Epoch: {self.__computors.epoch}')
                logging.info(f'Protocol: {self.__computors.protocol}')

            await asyncio.sleep(1)

    async def get_sub(self):
        if self._nc.is_disconected:
            return None

        return await self._nc.subscribe(Subjects.BROADCAST_COMPUTORS)

    async def _handler_msg(self, msg: Msg):
        if msg is None or len(msg.data) < sizeof(BroadcastComputors):
            return

        broadcast_computors = BroadcastComputors.from_buffer_copy(msg.data)
        self.__computors = broadcast_computors.computors


class HandleBroadcastResourceTestingSolution(Handler):
    def __init__(self, nc: Nats) -> None:
        super().__init__(nc)

        self.__scores = dict()

        self.add_task(asyncio.create_task(self.print_scores()))

    async def print_scores(self):
        while True:
            logging.info(f'Scores:\n{self.__scores}')
            await asyncio.sleep(1)

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
        new_score = get_score(
            bytes(resourceTestingSolution.nonces), NUMBER_OF_SOLUTION_NONCES)

        found_score = self.__scores.get(identity, 0)
        if found_score < new_score:
            self.__scores[identity] = new_score


class HandleBroadcastTick(Handler):
    def __init__(self, nc: Nats) -> None:
        super().__init__(nc)

        self.__ticks = dict()

        self.add_task(asyncio.create_task(self.print_ticks()))

    async def print_ticks(self):
        while True:
            logging.info(f'Ticks:\n{sorted(self.__ticks.keys())}')
            await asyncio.sleep(1)

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


async def main():
    logging.info('Start data processig')

    logging.info('Connecting to the nats server')

    nc = Nats()
    await nc.connect()

    logging.info('Subscribing to data')

    tasks = [
        asyncio.create_task(HandlerStarter.start(
            HandleBroadcastResourceTestingSolution(nc))),
        asyncio.create_task(HandlerStarter.start(HandleBroadcastTick(nc))),
        asyncio.create_task(HandlerStarter.start(HandleBroadcastComputors(nc)))
    ]

    await asyncio.wait(tasks)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
