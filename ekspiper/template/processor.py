import collections
from typing import List
import logging


logger = logging.getLogger(__name__)


ProcessCollectorsPair = collection.namedtuple(
    "ProcessCollectorsPair", [
        "processor",
        "collectors",
    ]
)


class TemplatizedProcessor:
    """
    Every ekspiper.Processor is associated with a corresponding set of ekspiper.Collectors.
    """

    def __init__(self,
        list_of_process_collectors_pair: List[ProcessCollectorsPair],
        output_collector: OutputCollector,
    ):
        self.output_collector = output_collector
        self.list_of_process_collectors_pair = list_of_process_collectors_pair

    async def aexecute(self,
        message_iterator,
    ):
        # go through all the messages
        async for message in message_iterator:

            # for all the process, collectors pair
            for pc in self.list_of_process_collectors_pair:

                output_messages = await pc.processor.aprocess(message)

                # run through the collectors for the corresponding
                # Collectors
                for m in output_messages:
                    for c in pc.processor.collectors:
                        await c.acollect_output(m)

                # if there is an output collector
                # collect the output as a whole
                if self.output_collector:
                    await self.output_collector.acollect(
                        input = message, 
                        output = output_messages,
                    )
