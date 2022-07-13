from ekspiper.template.processor import TemplateFlow, ProcessCollectorsMap
from ekspiper.processor.base import EntryProcessor
from ekspiper.collector.output import OutputCollector
from ekspiper.datasource.queue import QueueSource
from typing import Any
import asyncio
import unittest


class _TestStringProcessor(EntryProcessor):
    async def aprocess(self,
        entry: str,
    ) -> (str, str):
        return (entry + '_a', entry + '_b')


class _TestOutputCollector(OutputCollector):
    def __init__(self,
        prefix: str,
    ):
        self.prefix = prefix
        self.outputs = []

    async def acollect_output(self,
        entry: Any,
    ):
        self.outputs.append(self.prefix + entry)


class TemplateFlowTest(unittest.IsolatedAsyncioTestCase):
    
    async def test_template_processor(self):
        output_collectors = [
            _TestOutputCollector(prefix = "1::"),
            _TestOutputCollector(prefix = "2::"),
            _TestOutputCollector(prefix = "3::"),
        ]
        process_collectors_pairs = [
            ProcessCollectorsMap(
                processor = _TestStringProcessor(),
                collectors = output_collectors,
            )
        ]
        template_flow = TemplateFlow(
            process_collectors_maps = process_collectors_pairs
        )

        # prepare a few inputs
        async_queue = asyncio.Queue()
        async_queue.put_nowait("ONE")
        async_queue.put_nowait("TWO")
        async_queue.put_nowait("THREE")
        q = QueueSource(async_queue)
        
        # stop immediately to start the draining mode
        # so that we don't indefinitely wait
        q.stop() 

        await template_flow.aexecute(
            message_iterator = q,
        )

        expected_outputs = [
            ['1::ONE_a', '1::ONE_b', '1::TWO_a', '1::TWO_b', '1::THREE_a', '1::THREE_b'],
            ['2::ONE_a', '2::ONE_b', '2::TWO_a', '2::TWO_b', '2::THREE_a', '2::THREE_b'],
            ['3::ONE_a', '3::ONE_b', '3::TWO_a', '3::TWO_b', '3::THREE_a', '3::THREE_b']
        ]

        for c, expected_output in zip(output_collectors, expected_outputs):
            self.assertEqual(expected_output, c.outputs)