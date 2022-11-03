import asyncio
import logging
import zstandard
from ctypes import sizeof
from typing import Optional

import numpy
from algorithms.verify import get_score
from custom_nats.custom_nats import Nats
from custom_nats.handler import Handler, HandlerStarter
from nats.aio.msg import Msg
from qubic.qubicdata import (NUMBER_OF_COMPUTORS, BroadcastComputors,
                             BroadcastResourceTestingSolution, Computors,
                             DataSubjects, ResourceTestingSolution, Revenues,
                             Subjects, Tick)
from qubic.qubicutils import get_identities_from_computors, get_identity
from utils.backgroundtasks import BackgroundTasks


def _get_empty_revenues():
    return numpy.full((NUMBER_OF_COMPUTORS, NUMBER_OF_COMPUTORS), None, dtype=object).tolist()


class ItemContainer():
    def __init__(self) -> None:
        self._data = None
        self._file_name = None
        self._epoch = None

    @property
    def epoch(self) -> int:
        return self._epoch

    def add_data(self, *args, **kwargs) -> bool:
        try:
            self._epoch = int(kwargs['epoch'])
        except Exception as e:
            logging.exception(e)
            return False

        return True

    def clear(self):
        pass

    def is_empty(self):
        return True

    def dumps(self) -> str:
        import json
        if self._data is not None:
            return json.dumps(self._data)

    def loads(self, data):
        import json
        if data is not None and isinstance(data, str):
            self._data = json.loads(data)

    async def save_data(self):
        if self._file_name is None:
            logging.warning(
                f'{self.__class__.__name__}.save_data: file name is None')
            return

        if self._data is None:
            logging.warning(
                f'{self.__class__.__name__}.save_data: data is None')
            return

        data = self.dumps()
        if data is None:
            logging.warning(
                f'{self.__class__.__name__}.save_data: data from dumps is None')
            return

        if not isinstance(data, str):
            logging.warning(
                f'{self.__class__.__name__}.save_data: data from dumps is not str')
            return

        try:
            import aiofiles
            import json
            async with aiofiles.open(self._file_name, '+w') as f:
                await f.writelines([json.dumps({'epoch': self.epoch}) + '\n', data])
        except Exception as e:
            logging.exception(e)
            return

    async def load_from_file(self):
        if self._file_name is None:
            logging.warning(
                f'{self.__class__.__name__}.load_from_file: a file name is None')
            return

        import os.path
        if not os.path.exists(self._file_name):
            logging.info(
                f'{self.__class__.__name__}.load_from_file: a file is not exist')
            return

        try:
            import aiofiles
            import json

            async with aiofiles.open(self._file_name, 'r') as f:
                lines = f.readlines()
                self._epoch = json.loads(lines[0])
                self._data = json.loads(lines[1])
        except Exception as e:
            logging.exception(e)
            return

    async def delete_file(self):
        import aiofiles.os
        import os.path

        logging.info(f'{self.__class__.__name__}: Delets a file')

        if self._file_name is None:
            logging.warning(
                f'{self.__class__.__name__}.delete_file: a file name is None')
            return

        if not os.path.exists(self._file_name):
            logging.info(
                f'{self.__class__.__name__}.delte_file: a file is not exist')
            return

        try:
            await aiofiles.os.remove(self._file_name)
        except Exception as e:
            logging.exception(e)
            return


class ScoresIC(ItemContainer):
    SCORE_KEY = 's'
    TIMESTAMP_KEY = 't'

    def __init__(self) -> None:
        super().__init__()
        self._data = dict()
        self._file_name = 'scores.data'

    def __get_timestamp(self) -> int:
        from datetime import datetime
        return int(datetime.utcnow().replace(microsecond=0, second=0).timestamp())

    def add_data(self, *args, **kwargs):
        if super().add_data(*args, **kwargs) is False:
            return False

        try:
            identity = kwargs['identity']
            new_score = kwargs['score']
        except Exception as e:
            logging.exception(e)
            return False

        timestamp = self.__get_timestamp()
        found_score = self._data.setdefault(
            identity, {ScoresIC.SCORE_KEY: new_score, ScoresIC.TIMESTAMP_KEY: timestamp})[ScoresIC.SCORE_KEY]
        if found_score < new_score:
            self._data[identity] = {
                ScoresIC.SCORE_KEY: new_score, ScoresIC.TIMESTAMP_KEY: self.__get_timestamp()}
            return True

        return False

    def clear(self):
        self._data.clear()

    def is_empty(self):
        return len(self._data) <= 0


class DataContainer():
    __SEND_INTERVAL_S = 10
    __ticks = dict()
    __scores_ic = ScoresIC()
    __scores = dict()
    __btasks = BackgroundTasks()
    __computors: Optional[Computors] = None

    __revenues = _get_empty_revenues()

    __BACKUP_INTERVAL_S = 10
    __need_backup = False

    @classmethod
    def add_tick(cls, computor_index: int, new_tick: int):
        found_tick = cls.__ticks.setdefault(computor_index, new_tick)
        if found_tick < new_tick:
            cls.__ticks[computor_index] = new_tick

    @classmethod
    def add_scores(cls, identity, new_score: int):
        epoch = cls.get_epoch()
        if epoch is None:
            logging.warning(f'{cls.__name__}.add_scores: epoch is None')
            return

        if cls.__scores_ic.add_data(epoch=epoch, identity=identity, score=new_score):
            cls.__need_backup = True

    @classmethod
    def add_revenues(cls, index_sender: int, revenues: list):
        for idx, r in enumerate(revenues):
            cls.__revenues[idx][index_sender] = r

    @classmethod
    def add_computors(cls, computors: Computors):
        if cls.__computors is None or cls.__computors.epoch < computors.epoch:
            cls.__computors = computors
            cls.new_epoch(epoch=cls.__computors.epoch)

    @classmethod
    def new_epoch(cls, epoch: int):
        cls.__revenues = _get_empty_revenues()
        if cls.__scores_ic.epoch is None or epoch > cls.__scores_ic.epoch:
            cls.__scores_ic.clear()
            cls.__btasks.create_task(cls.__scores_ic.delete_file)

        cls.__ticks.clear()

    @classmethod
    async def recovery(cls):
        logging.info(f'{cls.__name__}: Recovery')

        await cls.__scores_ic.load_from_file()

    @classmethod
    async def backup_loop(cls):
        logging.info('Backup')
        tasks = []
        if cls.__need_backup:
            cls.__need_backup = False

            logging.info('Backing up')

            tasks.append(cls.__btasks.create_task(cls.__scores_ic.save_data))

        if len(tasks) > 0:
            await asyncio.wait(tasks)

        await asyncio.wait(cls.__BACKUP_INTERVAL_S)
        cls.__btasks.create_task(cls.backup_loop)

    @classmethod
    def get_ticks(cls) -> dict:
        return cls.__ticks

    @classmethod
    def get_revenues(cls) -> dict:
        if cls.__computors is None:
            return dict()

        pretty_revenues = dict()
        identities = get_identities_from_computors(cls.__computors)
        for idx, r_list in enumerate(cls.__revenues):
            pretty_revenues[identities[idx]] = sorted(
                [rev for rev in r_list if rev is not None])

        return pretty_revenues

    @classmethod
    def get_epoch(cls) -> int | None:
        if cls.__computors is None:
            return None

        return cls.__computors.epoch

    @classmethod
    async def send_data(cls):
        import json

        nc = Nats()
        if nc.is_disconected:
            logging.error(f'{DataContainer.__name__}: Nats is disconected')
            return

        while not nc.is_disconected:
            tasks = set()
            tasks.add(asyncio.create_task(
                asyncio.sleep(cls.__SEND_INTERVAL_S)))

            tick_number = len(cls.__ticks)
            if tick_number > 0:
                logging.info(f'Send ticks')
                tasks.add(cls.__btasks.create_task(nc.publish,
                                                   DataSubjects.TICKS, json.dumps(cls.__ticks).encode()))

            if not cls.__scores_ic.is_empty():
                logging.info(f'Send scores:\n{cls.__scores_ic.dumps()}')
                tasks.add(cls.__btasks.create_task(
                    nc.publish, DataSubjects.SCORES, cls.__scores_ic.dumps().encode()))

            epoch = cls.get_epoch()
            if epoch is not None:
                logging.info(f'Send epoch: {epoch}')
                tasks.add(cls.__btasks.create_task(
                    nc.publish, DataSubjects.EPOCH, json.dumps(epoch).encode()))

            try:
                revenues = cls.get_revenues()
                if len(revenues) > 0:
                    logging.info(f'Send revenues')
                    compressed_revenues = zstandard.compress(
                        json.dumps(revenues).encode())
                    tasks.add(cls.__btasks.create_task(nc.publish,
                                                       DataSubjects.REVENUES, compressed_revenues))
            except Exception as e:
                logging.exception(e)

            await asyncio.wait(tasks)


class HandleBroadcastComputors(Handler):
    def __init__(self, nc: Nats) -> None:
        super().__init__(nc)

    async def get_sub(self):
        if self._nc.is_disconected:
            return None

        return await self._nc.subscribe(Subjects.BROADCAST_COMPUTORS)

    async def _handler_msg(self, msg: Msg):
        if msg is None or len(msg.data) < sizeof(BroadcastComputors):
            return

        try:
            logging.info('Got computors')
            DataContainer.add_computors(
                BroadcastComputors.from_buffer_copy(msg.data).computors)
        except Exception as e:
            logging.exception(e)
            return


class HandleBroadcastResourceTestingSolution(Handler):
    def __init__(self, nc: Nats) -> None:
        super().__init__(nc)

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

        logging.info('Got scores')
        try:
            broadcastResourceTestingSolution = BroadcastResourceTestingSolution.from_buffer_copy(
                data)
        except Exception as e:
            logging.exception(e)
            return
        resourceTestingSolution: ResourceTestingSolution = broadcastResourceTestingSolution.resourceTestingSolution
        identity = get_identity(
            bytes(resourceTestingSolution.computorPublicKey))
        new_score = get_score(resourceTestingSolution.nonces)

        DataContainer.add_scores(identity=identity, new_score=new_score)


class HandlerRevenues(Handler):
    async def get_sub(self):
        if self._nc.is_disconected:
            return None

        return await self._nc.subscribe(Subjects.BROADCAST_REVENUES)

    async def _handler_msg(self, msg: Msg):
        if msg is None or len(msg.data) <= 0:
            return

        data = msg.data

        try:
            revenues = Revenues.from_buffer_copy(data)
        except Exception as e:
            logging.exception(e)
            return

        DataContainer.add_revenues(
            revenues.computorIndex, list(revenues.revenues))


class HandleBroadcastTick(Handler):
    def __init__(self, nc: Nats) -> None:
        super().__init__(nc)

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

    await DataContainer.recovery()

    tasks = [
        asyncio.create_task(HandlerStarter.start(
            HandleBroadcastResourceTestingSolution(nc))),
        asyncio.create_task(HandlerStarter.start(
            HandleBroadcastTick(nc))),
        asyncio.create_task(HandlerStarter.start(
            HandleBroadcastComputors(nc))),
        asyncio.create_task(HandlerStarter.start(
            HandlerRevenues(nc))),
        asyncio.create_task(DataContainer.backup_loop()),
        asyncio.create_task(DataContainer.send_data())
    ]

    await asyncio.wait(tasks)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
