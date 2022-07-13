import collections
from typing import List
import logging
from ekspiper.collector.output import OutputCollector
from ekspiper.processor.base import RetryWrapper


logger = logging.getLogger(__name__)


ProcessCollectorsMap = collections.namedtuple(
    "ProcessCollectorsMap", [
        "processor",
        "collectors",
    ]
)


class TemplateFlow:
    """
    Every ekspiper.Processor is associated with a corresponding set of ekspiper.Collectors.
    """

    def __init__(self,
        process_collectors_maps: List[ProcessCollectorsMap],
        output_collector: OutputCollector = None,
    ):
        self.output_collector = output_collector
        self.process_collectors_maps = process_collectors_maps

    async def aexecute(self,
        message_iterator,
    ):
        retry_wrapper = RetryWrapper()

        # go through all the messages
        async for message in message_iterator:

            # for all the process, collectors pair
            for pc in self.process_collectors_maps:

                output_messages = await retry_wrapper.aretry(
                    message,
                    pc.processor.aprocess,
                )

                # run through the collectors for the corresponding
                # Collectors
                for m in output_messages:
                    for c in pc.collectors:
                        await c.acollect_output(m)

                # if there is an output collector
                # collect the output as a whole
                if self.output_collector:
                    await self.output_collector.acollect(
                        input = message, 
                        output = output_messages,
                    )
