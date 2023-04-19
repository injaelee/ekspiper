import asyncio
import sys
import traceback

from ekspiper.util.callable import RetryWrapper
from xrpl.asyncio.clients import (
    AsyncWebsocketClient,
    AsyncJsonRpcClient,
)
from xrpl.models import Subscribe, StreamParameter
from xrpl.models.requests.ledger_data import LedgerData
from typing import Callable, Union
import logging
import bson
from .data import DataSource
from ..util.async_iterable_with_timeout import AsyncTimedIterable

logger = logging.getLogger(__name__)


class LedgerCreationDataSource(DataSource):
    def __init__(self,
        wss_url: str = "wss://s1.ripple.com",
        done_callback: Callable[[], None] = None,
        stream_type = StreamParameter.LEDGER,
    ):
        self.wss_url = wss_url
        self.async_queue = asyncio.Queue()
        self.is_stop = False
        self.populate_task = None
        self.client = None
        self.done_callback = done_callback
        self.stream_type = stream_type

    async def _start(self):
        ledger_update_sub_req = Subscribe(streams=[self.stream_type])

        async with AsyncWebsocketClient(self.wss_url) as client:
            self.client = client
            # one time subscription
            logger.info("[LedgerCreationDataSource] Sending subscribe request")
            await client.send(ledger_update_sub_req)

            try:
                timed_message_iterator = AsyncTimedIterable(client, 15)
                async for message in timed_message_iterator:
                    self.async_queue.put_nowait(message)
            except asyncio.TimeoutError as e:
                logger.error("[LedgerCreationDataSource] Haven't received a message in 15s, closing connection : " + str(e))
                await client.close()
            except Exception as e:
                logger.error("[LedgerCreationDataSource] Uncaught exception type: " + str(e))

        logger.warning("[LedgerCreationDataSource] Connection closed - server kicked us off")

    def stop(self):
        self.is_stop = True
        self.client.close()

        if self.populate_task:
            self.populate_task.cancel()

    def __aiter__(self):
        return self

    async def __anext__(self):
        # TODO: refactor to abstract method
        if self.is_stop and self.async_queue.empty():
            try:
                if self.done_callback:
                    self.done_callback()
            except Exception as e:
                traceback.print_exc(file = sys.stdout)
            finally:
                raise StopAsyncIteration

        return await self.async_queue.get()


class LedgerObjectDataSource(DataSource):
    def __init__(self,
        rpc_client: AsyncJsonRpcClient,
        ledger_index: Union[int,str] = "current",
        is_attach_execution_id: bool = True,
        is_attach_seq: bool = True,
        done_callback: Callable[[], None] = None,
    ):
        # more than efficient for a request-response query pattern
        #  - server is not pushing any information; must have a request
        #  - make sure HTTP keep-alive to avoid reconnect/establishment
        self.rpc_client = rpc_client

        self.ledger_index = ledger_index
        self.next_marker = None

        self.async_queue = asyncio.Queue()
        self.is_stop = False

        self.is_attach_execution_id = is_attach_execution_id
        self.is_attach_seq = is_attach_seq

        self.message_sequence = 0
        self.execution_id = str(bson.ObjectId())

        self.done_callback = done_callback

    def start(self):
        self.populate_task = asyncio.create_task(self._start())

    async def _start(self):
        retry_wrapper = RetryWrapper()

        next_marker = None
        ledger_index = self.ledger_index
        while not self.is_stop:

            response = await retry_wrapper.aretry(
                LedgerData(
                    ledger_index = self.ledger_index,
                    marker = next_marker,
                ),
                self.rpc_client.request,
            )

            # check whether the message was successful and retry
            if not response.is_successful():
                logging.error("[FAILED] response: %s", response)
                continue

            result = response.result
            ledger_index = result.get('ledger_index')
            next_marker = result.get('marker')
            list_of_ledger_objs = result.get('state', [])

            for ledger_obj in list_of_ledger_objs:

                # append metadata
                ledger_obj['_LedgerIndex'] = int(ledger_index)

                if self.is_attach_execution_id:
                    ledger_obj['_ExecutionID'] = self.execution_id

                if self.is_attach_seq:
                    ledger_obj['_Sequence'] = self.message_sequence
                    self.message_sequence += 1

                logger.debug(
                    "[LedgerObjectDataSource] seq:%d putting ledger obj into queue",
                    self.message_sequence,
                )
                await self.async_queue.put(ledger_obj)

            # put into auto stop if last marker
            if not next_marker:
                self.is_stop = True
                break

        logger.info("[LedgerObjectDataSource] exiting extraction loop")

    def stop(self):
        self.is_stop = True
        self.populate_task.cancel()

    def __aiter__(self):
        return self

    async def __anext__(self):
        # TODO: refactor to abstract method
        if self.is_stop and self.async_queue.empty():
            try:
                if self.done_callback:
                    self.done_callback()
            except Exception as e:
                traceback.print_exc(file = sys.stdout)
            finally:
                raise StopAsyncIteration

        return await self.async_queue.get()
