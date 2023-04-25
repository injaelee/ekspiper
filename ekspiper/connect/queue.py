import asyncio
import logging
import sys
import traceback
from typing import Callable

from .data import DataSource, DataSink

logger = logging.getLogger(__name__)


class QueueSourceSink(DataSource, DataSink):
    def __init__(self,
                 async_queue: asyncio.Queue = None,
                 name: str = "",
                 done_callback: Callable[[], None] = None,
                 ):
        self.name = name
        self.async_queue = async_queue if async_queue else asyncio.Queue()
        self.is_stop = False
        self.done_callback = done_callback

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
            try:
                if self.done_callback:
                    self.done_callback()
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
            finally:
                raise StopAsyncIteration

        return await self.async_queue.get()

    async def put(self,
                  entry,
                  ):
        await self.async_queue.put(entry)
