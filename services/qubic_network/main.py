import asyncio
import logging
from typing import Any
from custom_nats.custom_nats import Nats

from qubic.qubicdata import Computors, Subjects, ExchangePublicPeers
from manager import QubicNetworkManager
from qubic.qubicdata import BROADCAST_COMPUTORS, EXCHANGE_PUBLIC_PEERS


async def publish_data(header_type: int, data: Any):
    nc = await Nats().connect()
    if nc is None:
        logging.error('Failed to connect to Nats')
        return

    logging.debug('publish_data')

    if header_type == BROADCAST_COMPUTORS and isinstance(data, Computors):
        logging.debug('broadcast')
        payload = bytes(data)
        
        await nc.publish(Subjects.BROADCAST_COMPUTORS, payload=payload)
    elif header_type == EXCHANGE_PUBLIC_PEERS and isinstance(data, ExchangePublicPeers):
        logging.debug('public_peers')
        payload = bytes(data)

        try:
            await nc.publish(Subjects.EXCHANGE_PUBLIC_PEERS, payload=payload)
        except asyncio.CancelledError as e:
            raise e
        except Exception as e:
            logging.warning(e)


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