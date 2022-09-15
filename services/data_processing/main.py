import asyncio
import itertools
import logging
from ctypes import sizeof
from typing import Optional

from algorithms.verify import get_score
from custom_nats.custom_nats import Nats
from custom_nats.handler import Handler, HandlerStarter
from nats.aio.msg import Msg
from qubic.qubicdata import (NUMBER_OF_SOLUTION_NONCES, BroadcastComputors,
                             BroadcastResourceTestingSolution, Computors,
                             ResourceTestingSolution, Subjects, Tick, DataSubjects)
from qubic.qubicutils import get_identity


class DataContainer():
    __ticks = dict()
    __SEND_INTERVAL_S = 10

    @classmethod
    def add_tick(cls, computor_index: int, new_tick: int):
        found_tick = cls.__ticks.setdefault(computor_index, new_tick)
        if found_tick < new_tick:
            cls.__ticks[computor_index] = new_tick

    @classmethod
    def get_ticks(cls) -> dict:
        return cls.__ticks

    @classmethod
    async def send_data(cls):
        import json

        nc = Nats()
        if nc.is_disconected:
            logging.error(f'{DataContainer.__name__}: Nats is disconected')
            return

        while not nc.is_disconected:
            logging.info('Sending data')
            tasks = set()
            tasks.add(asyncio.create_task(
                asyncio.sleep(cls.__SEND_INTERVAL_S)))

            if len(cls.__ticks) >= 0:
                tasks.add(asyncio.create_task(nc.publish(DataSubjects.TICKS,
                                                         json.dumps(cls.__ticks).encode())))

            await asyncio.wait(tasks)


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

        self.add_task(asyncio.create_task(self.print_ticks()))

    async def print_ticks(self):
        while True:
            sorted_ticks = sorted(
                DataContainer.get_ticks().values(), reverse=True)
            pretty_ticks = [(key, len(list(group)))
                            for key, group in itertools.groupby(sorted_ticks)]
            logging.info(f'Ticks:\n{pretty_ticks}')
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

        DataContainer.add_tick(
            tick_structure.computorIndex, tick_structure.tick)


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
        asyncio.create_task(HandlerStarter.start(
            HandleBroadcastComputors(nc))),
        asyncio.create_task(DataContainer.send_data())
    ]

    await asyncio.wait(tasks)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
