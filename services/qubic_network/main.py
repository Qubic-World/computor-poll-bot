import asyncio
import logging
from typing import Any
from custom_nats.custom_nats import Nats

from qubic.qubicdata import Computors, Subjects
from manager import QubicNetworkManager
from qubic.qubicdata import BROADCAST_COMPUTORS


async def publish_data(type: int, data: Any):
    nc = await Nats().connect()
    if nc is None:
        logging.error('Failed to connect to Nats')
        return

    if type == BROADCAST_COMPUTORS and isinstance(data, Computors):
        computors: Computors = data
        payload = bytes(computors)
        
        await nc.publish(Subjects.BROADCAST_COMPUTORS, payload=payload)


async def main():

    nc = await Nats().connect()
    if nc is None:
        logging.error('Failed to connect to Nats')
        return

    qubic = QubicNetworkManager(["213.127.147.70",
                               "83.57.175.137",
                               "178.172.194.130",
                               "82.114.88.225",
                               "82.223.197.126",
                               "82.223.165.100",
                               "85.215.98.91",
                               "212.227.149.43"])

    qubic.add_callback

    try:
        await asyncio.wait(qubic.start())
    finally:
        await qubic.stop()

    

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())