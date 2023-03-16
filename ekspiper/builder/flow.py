from __future__ import annotations
import asyncio
import logging

from ekspiper.template.processor import (
    ProcessCollectorsMap, 
    TemplateFlow,
)
from ekspiper.processor.base import EntryProcessor
from ekspiper.collector.output import (
    FluentCollector,
    OutputCollector,
    STDOUTCollector,
    QueueCollector,
    DataSinkCollector, BigQueryCollector,
)
from fluent.asyncsender import FluentSender


class ProcessCollectorsMapBuilder:
    def __init__(self):
        self.processor: EntryProcessor = None
        self.output_collectors: List[OutputCollector] = []

    def with_processor(self,
        processor: EntryProcessor,
    ) -> ProcessCollectorsMapBuilder:
        if self.processor:
            raise ValueError("EntryProcessor already defined: %s" % self.processor)
        self.processor = processor
        return self

    def add_async_queue_output_collector(self,
        async_queue: asyncio.Queue,
        name: str = None,
    ) -> ProcessCollectorsMapBuilder:
        self.output_collectors.append(QueueCollector(
            async_queue = async_queue,
            name = name,
        ))
        return self

    def add_data_sink_output_collector(self,
        data_sink: DataSink,
        name: str = None,
    ) -> ProcessCollectorsMapBuilder:
        self.output_collectors.append(DataSinkCollector(
            data_sink = data_sink,
            name = name,
        ))
        return self

    def add_fluent_output_collector(self,
        tag_name: str,
        fluent_sender: FluentSender,
    ) -> ProcessCollectorsMapBuilder:
        logging.warning("adding fluent collector")
        self.output_collectors.append(FluentCollector(
            fluent_sender = fluent_sender,
            tag_name = tag_name,
        ))
        return self

    def add_bigquery_output_collector(self, project: str, dataset: str, table: str) -> ProcessCollectorsMapBuilder:
        self.output_collectors.append(BigQueryCollector(project=project, dataset=dataset, table=table))
        return self


    def with_stdout_output_collector(self,
        tag_name: str = "",
        is_simplified: bool = False,
    ) -> ProcessCollectorsMapBuilder:
        self.output_collectors.append(STDOUTCollector(
            tag_name = tag_name,
            is_simplified = is_simplified,
        ))
        return self

    def build(self) -> ProcessCollectorsMap:
        return ProcessCollectorsMap(
            processor = self.processor,
            collectors = self.output_collectors,
        )


class TemplateFlowBuilder:
    def __init__(self):
        self.process_collectors_maps = []

    def add_process_collectors_map(self,
        process_collectors_map: ProcessCollectorsMap,
    ) -> TemplateFlowBuilder:
        self.process_collectors_maps.append(process_collectors_map)
        return self

    def build(self) -> TemplateFlow:
        return TemplateFlow(
            process_collectors_maps = self.process_collectors_maps,
        )
