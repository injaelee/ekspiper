import asyncio
import logging

import aiofiles as aiofiles

from .data import DataSource

logger = logging.getLogger(__name__)


class FileDataSource(DataSource):
    def __init__(self,
                 file: str,
                 ):
        self.async_queue = asyncio.Queue()
        self.is_stop = False
        self.populate_task = None
        self.file = file

    def start(self):
        self.populate_task = asyncio.create_task(self._start())

    async def _start(self):
        if not self.is_stop:
            async with aiofiles.open(self.file, mode='r') as f:
                async for line in f:
                    try:
                        ledger = int(line)
                        await self.async_queue.put(ledger)  # cast to int and add
                        await asyncio.sleep(0)  # force yielding control
                    except Exception as e:
                        logger.exception(e)
                        logger.error("[FileDataSource] Couldnt cast line to int ", line)

    def stop(self):
        self.is_stop = True
        self.populate_task.cancel()

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.is_stop and self.async_queue.empty():
            raise StopAsyncIteration

        return await self.async_queue.get()
