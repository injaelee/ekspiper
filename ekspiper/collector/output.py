from fluent.asyncsender import FluentSender
from typing import Any, Dict, List
import asyncio
import logging


logger = logging.getLogger(__name__)


class OutputCollector:
    async def acollect_output(self,
        entry: Any,
    ):
        return


class FluentCollector(OutputCollector):
    def __init__(self,
        fluent_sender: FluentSender,
        tag_name: str,
    ):
        self.tag_name = tag_name
        self.fluent_sender = fluent_sender

    async def acollect_output(self,
        entry: Dict[str, Any]
    ):
        logger.info("[FluentCollector] pre-emit")
        is_emitted = self.fluent_sender.emit(
            self.tag_name, 
            entry,
        )
        logger.info("[FluentCollector] emit done: %s", is_emitted)


class LoggerCollector(OutputCollector):
    async def acollect_output(self,
        entry: Dict[str, Any]
    ):
        logger.info("[LoggerCollector] %s", entry)


class STDOUTCollector(OutputCollector):
    def __init__(self,
        tag_name: str = "",
        is_simplified: bool = False,
    ):
        self.tag_name = tag_name
        self.is_simplified = is_simplified

    async def acollect_output(self,
        entry: Dict[str, Any]
    ):
        if self.is_simplified:
            if type(entry) == dict:
                print("[STDOUTCollector::%s] Received entry keys: %s" % (
                    self.tag_name,
                    entry.keys(),
                ))
        else:
            print("[STDOUTCollector::%s] %s" % (
                self.tag_name,
                entry,
            ))


class MetricCollector(OutputCollector):
    async def acollect_output(self,
        entry: Dict[str, Any]
    ):
        return


class QueueCollector(OutputCollector):
    def __init__(self,
        async_queue: asyncio.Queue,
        name:str = None,
    ):
        self.async_queue = async_queue
        self.name = "" if not name else name

    async def acollect_output(self,
        entry: Dict[str, Any]
    ):
        logger.debug("[QueueCollector:%s] pre-put entry", self.name)
        await self.async_queue.put(entry)
        logger.debug("[QueueCollector:%s] post-put entry", self.name)
