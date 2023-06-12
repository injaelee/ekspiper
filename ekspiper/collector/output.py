import asyncio
import logging
from typing import Any, Dict

from fluent.asyncsender import FluentSender
from google.cloud import bigquery

from ekspiper.connect.data import DataSink

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class OutputCollector:
    async def acollect_output(self,
                              entry: Any,
                              ):
        return


class BigQueryCollector(OutputCollector):
    def __init__(self, project: str, dataset: str, table: str):
        self.project = project
        self.table = table
        self.dataset = dataset

    async def acollect_output(self,
                              entry: Dict[str, Any]
                              ):
        table_id = self.project + "." + self.dataset + "." + self.table

        errors = bigquery.Client().insert_rows_json(table_id, [entry], row_ids=[None] * len([entry]))

        if not errors:
            logger.info("[BigQueryCollector] New rows have been added.")
        else:
            logger.warning("[BigQueryCollector] Encountered errors while inserting rows: {}".format(errors))


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
        logger.debug("[FluentCollector] pre-emit")
        is_emitted = self.fluent_sender.emit(
            self.tag_name,
            entry,
        )
        logger.debug("[FluentCollector] emit done: %s", is_emitted)


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
                 name: str = None,
                 ):
        self.async_queue = async_queue
        self.name = "" if not name else name

    async def acollect_output(self,
                              entry: Dict[str, Any]
                              ):
        logger.debug("[QueueCollector:%s] pre-put entry", self.name)
        await self.async_queue.put(entry)
        logger.debug("[QueueCollector:%s] post-put entry", self.name)


class DataSinkCollector(OutputCollector):
    def __init__(self,
                 data_sink: DataSink,
                 name: str = None,
                 ):
        self.data_sink = data_sink
        self.name = "" if not name else name

    async def acollect_output(self,
                              entry: Dict[str, Any]
                              ):
        await self.data_sink.put(entry)
