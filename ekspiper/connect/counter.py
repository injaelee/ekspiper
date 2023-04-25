import asyncio
import logging

from .data import DataSource

logger = logging.getLogger(__name__)


class PartitionedCounterDataSource(DataSource):
    def __init__(self,
                 starting_count: int,
                 shard_index: int,
                 shard_size: int,
                 incr_by: int = -1,
                 ):
        self.async_queue = asyncio.Queue()
        self.is_stop = False
        self.populate_task = None

        self.shard_index = shard_index
        self.shard_size = shard_size
        self.current_index = starting_count
        self.incr_by = incr_by

    def start(self):
        self.populate_task = asyncio.create_task(self._start())

    async def _start(self):
        while self.current_index > 0 and not self.is_stop:

            if self.current_index % self.shard_size != self.shard_index:
                self.current_index += self.incr_by
                continue

            idx = self.current_index
            self.current_index += self.incr_by
            await self.async_queue.put(idx)
            await asyncio.sleep(0)  # force yielding control

    def stop(self):
        self.is_stop = True
        self.populate_task.cancel()

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.is_stop and self.async_queue.empty():
            raise StopAsyncIteration

        return await self.async_queue.get()
