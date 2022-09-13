import asyncio
import logging
from typing import Any

from custom_nats.custom_nats import Nats
from qubic.qubicdata import (BROADCAST_COMPUTORS,
                             BROADCAST_RESOURCE_TESTING_SOLUTION,
                             BROADCAST_TICK, EXCHANGE_PUBLIC_PEERS,
                             BroadcastResourceTestingSolution, BroadcastComputors,
                             ExchangePublicPeers, Subjects, Tick)

from manager import QubicNetworkManager


async def publish_data(header_type: int, data: Any):
    nc = Nats()
    if await nc.connect() is None:
        logging.error('Failed to connect to Nats')
        return

    if header_type == BROADCAST_COMPUTORS and isinstance(data, BroadcastComputors):
        # logging.debug('BROADCAST_COMPUTORS')
        payload = bytes(data)

        await nc.publish(Subjects.BROADCAST_COMPUTORS, payload=payload)
    elif header_type == EXCHANGE_PUBLIC_PEERS and isinstance(data, ExchangePublicPeers):
        # logging.debug('EXCHANGE_PUBLIC_PEERS')
        payload = bytes(data)

        await nc.publish(Subjects.EXCHANGE_PUBLIC_PEERS, payload=payload)
    elif header_type == BROADCAST_RESOURCE_TESTING_SOLUTION and isinstance(data, BroadcastResourceTestingSolution):
        # logging.debug('BROADCAST_RESOURCE_TESTING_SOLUTION')
        await nc.publish(Subjects.BROADCAST_RESOURCE_TESTING_SOLUTION, bytes(data))
    elif header_type == BROADCAST_TICK and isinstance(data, Tick):
        # logging.debug('BROADCAST_TICK')
        await nc.publish(Subjects.BROADCAST_TICK, payload=bytes(data))


async def main():

    nc = await Nats().connect()
    if nc is None:
        logging.error('Failed to connect to Nats')
        return

    qubic = QubicNetworkManager(["93.125.105.208", "178.172.194.154", "91.43.75.241", "178.172.194.148", "178.172.194.130",
                                 "178.172.194.150", "178.172.194.147"])

    qubic.add_callback(publish_data)

    try:
        await qubic.start()
    finally:
        await qubic.stop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
