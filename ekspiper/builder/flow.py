import asyncio
from ekspiper.template.processor import ProcessCollectorsMap
from ekspiper.processor.base import EntryProcessor
from ekspiper.collector.output import (
    OutputCollector,
    STDOUTCollector,
)
from fluent.asyncsender import FluentSender


class ProcessCollectorsMapBuilder:
    def __init__(self):
        self.processor: EntryProcessor = None
        self.output_collectors: List[OutputCollector] = []

    def with_processor(self,
        processor: EntryProcessor,
    ):
        if self.processor:
            raise ValueError("EntryProcessor already defined: %s" % self.processor)
        self.processor = processor
        return self

    def add_async_queue_output_collector(self,
        async_queue: asyncio.Queue,
    ):
        self.output_collectors.append(QueueCollector(
            async_queue = async_queue,
        ))
        return self

    def add_fluent_output_collector(self,
        tag_name: str,
        fluent_sender: FluentSender,
    ):
        self.output_collectors.append(FluentCollector(
            fluent_sender = fluent_sender,
            tag_name = tag_name,
        ))
        return self

    def with_stdout_output_collector(self):
        self.output_collectors.append(STDOUTCollector())
        return self

    def build(self) -> ProcessCollectorsMap:
        return None


class TemplateFlowBuilder:
    def __init__(self):
        self.process_collectors_maps = []

    def add_process_collectors_map(self,
        process_collectors_map: ProcessCollectorsMap,
    ) -> None;
        self.process_collectors_maps.append(process_collectors_map)
        return self

    def build(self) -> TemplateFlow:
        return TemplateFlow(
            process_collectors_maps = self.process_collectors_maps,
        )
