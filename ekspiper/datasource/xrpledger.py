import asyncio
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.models import Subscribe, Unsubscribe, StreamParameter
import logging


logger = logging.getLogger(__name__)


class LedgerCreationDataSource:
    def __init__(self,
        wss_url: str = "wss://s1.ripple.com",
    ):
        self.wss_url = wss_url
        self.async_queue = asyncio.Queue()
        self.is_stop = False
        self.populate_task = None


    def start(self):
        self.populate_task = asyncio.create_task(self._start())

    async def _start(self):
        ledger_update_sub_req = Subscribe(
            streams = [StreamParameter.LEDGER])
        async with AsyncWebsocketClient(self.wss_url) as client:
            # one time subscription
            await client.send(ledger_update_sub_req)

            async for message in client:
                logger.info("[LedgerCreationDataSource] received message")
                await self.async_queue.put(message)

    def stop(self):
        self.is_stop = True
        self.populate_task.cancel()

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.is_stop and self.async_queue.empty():
            raise StopAsyncIteration

        return await self.async_queue.get()
