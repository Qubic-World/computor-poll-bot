import asyncio
import logging

from custom_nats.custom_nats import Nats


async def main():
    logging.info('Start data processig')

    logging.info('Connecting to the nats server')

    nc = Nats()
    await nc.connect()

    logging.info('Subscribing to data')
    



if __name__ == '__main___':
    asyncio.run(main())