import logging
from fluent.asyncsender import FluentSender


logger = logging.getLogger(__name__)


class Collector:
    async def acollect(self,
        entry: Any,
    ):
        return


class FluentCollector(Collector):
    def __init__(self,
        fluent_sender: FluentSender,
        tag_name: str,
    ):
        self.tag_name = tag_name
        self.fluent_sender = fluent_sender

    async def acollect(self,
        entry: Dict[str, Any]
    ):
        logger.info("[FluentCollector] pre-emit")
        await self.fluent_sender.emit(
            self.tag_name, 
            entry,
        )
        logger.info("[FluentCollector] emit done")


class LoggerCollector(Collector):
    async def acollect(self,
        entry: Dict[str, Any]
    ):
        logger.info("[LoggerCollector] %s", entry)


class MetricCollector(Collector):
    async def acollect(self,
        entry: Dict[str, Any]
    ):
        return


class QueueCollector(Collector):
    def __init__(self,
        async_queue: asyncio.Queue,
    ):
        self.async_queue = async_queue

    async def acollect(self,
        entry: Dict[str, Any]
    ):
        await async_queue.put(entry)