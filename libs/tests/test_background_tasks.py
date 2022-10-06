

import asyncio
import logging
import unittest

from utils.backgroundtasks import BackgroundTasks


class TestBackgroundTasks(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    async def coro_for_test():
        await asyncio.sleep(10)

    @classmethod
    async def coro_execute(cls):
        await asyncio.sleep(0)

    async def test_background_tasks(self):
        b = BackgroundTasks()

        NUMBER_OF_TASKS = 5
        for _ in range(0, NUMBER_OF_TASKS):
            b.create_task(TestBackgroundTasks.coro_for_test)

        self.assertEqual(NUMBER_OF_TASKS, len(b), 'Failed to create all tasks')
        await asyncio.sleep(0)
        await b.close()
        self.assertEqual(0, len(b), 'Failed to complete all tasks')

        await b.create_and_wait(self.coro_execute)
        self.assertEqual(0, len(b), 'Failed to complete all tasks')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        unittest.main()
    finally:
        pass
