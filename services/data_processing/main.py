import asyncio
import logging
from ctypes import sizeof

from algorithms.verify import get_score
from custom_nats.custom_nats import Nats
from custom_nats.handler import Handler, HandlerStarter
from qubic.qubicdata import (NUMBER_OF_SOLUTION_NONCES,
                             BroadcastResourceTestingSolution,
                             ResourceTestingSolution, Subjects)
from qubic.qubicutils import get_identity


class HandleBroadcastResourceTestingSolution(Handler):
    async def get_sub(self):
        if self._nc.is_disconected:
            return None

        return await self._nc.subscribe(Subjects.BROADCAST_RESOURCE_TESTING_SOLUTION)

    async def _handler_msg(self, msg):
        self._info('Handling BroadcastResourceTestingSolution')

        if msg is None:
            return None

        if len(msg) != sizeof(BroadcastResourceTestingSolution):
            self._warning(
                'BroadcastResourceTestingSolution structure size does not match payload size')
            return None

        broadcastResourceTestingSolution = BroadcastResourceTestingSolution.from_buffer_copy(
            msg)
        resourceTestingSolution: ResourceTestingSolution = broadcastResourceTestingSolution.resourceTestingSolution
        identity = get_identity(
            bytes(resourceTestingSolution.computorPublicKey))
        score = get_score(
            bytes(resourceTestingSolution.nonces), NUMBER_OF_SOLUTION_NONCES)

        logging.info(
            f'BroadcastResourceTestingSolution: {identity} -- {score}')


async def main():
    logging.info('Start data processig')

    logging.info('Connecting to the nats server')

    nc = Nats()
    await nc.connect()

    logging.info('Subscribing to data')

    tasks = [
        asyncio.create_task(HandlerStarter.start(
            HandleBroadcastResourceTestingSolution(nc)))
    ]

    await asyncio.wait(tasks)


if __name__ == '__main___':
    asyncio.run(main())
