import asyncio
import logging
from typing import Generic, TypeVar
from .data import DataSource, DataSink


logger = logging.getLogger(__name__)


class QueueSourceSink(DataSource, DataSink):
    def __init__(self,
        async_queue: asyncio.Queue = None,
        name: str = "",
    ):
        self.name = name
        self.async_queue = async_queue if async_queue else asyncio.Queue()
        self.is_stop = False

    def stop(self):
        self.is_stop = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        logging.debug(
            "Queue '%s' length: %d", 
            self.name,
            self.async_queue.qsize(),
        )
        if self.is_stop and self.async_queue.empty():
            raise StopAsyncIteration

        return await self.async_queue.get()

    async def put(self,
        entry,
    ):
        await self.async_queue.put(entry)

