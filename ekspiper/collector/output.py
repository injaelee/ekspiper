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
        await self.fluent_sender.emit(
            self.tag_name, 
            entry,
        )
        logger.info("[FluentCollector] emit done")


class LoggerCollector(OutputCollector):
    async def acollect_output(self,
        entry: Dict[str, Any]
    ):
        logger.info("[LoggerCollector] %s", entry)


class STDOUTCollector(OutputCollector):
    async def acollect_output(self,
        entry: Dict[str, Any]
    ):
        print("[STDOUTCollector] %s" % entry)


class MetricCollector(OutputCollector):
    async def acollect_output(self,
        entry: Dict[str, Any]
    ):
        return


class QueueCollector(OutputCollector):
    def __init__(self,
        async_queue: asyncio.Queue,
    ):
        self.async_queue = async_queue

    async def acollect_output(self,
        entry: Dict[str, Any]
    ):
        await async_queue.put(entry)
