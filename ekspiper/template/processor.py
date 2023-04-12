import collections
import time
from typing import List
import logging
from ekspiper.collector.output import OutputCollector
from ekspiper.util.callable import RetryWrapper

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

    async def aexecute(self, message_iterator):
        try:
            await self._aexecute(message_iterator)
        except Exception as e:
            logger.error("[Template Flow] - Uncaught Error while executing processors: " + str(e))

    async def _aexecute(self, message_iterator):
        if not message_iterator:
            raise ValueError("message_iterator is not specified")

        retry_wrapper = RetryWrapper()
        # should_stop = False
        # ripple_epoch = 946684800
        # epoch_time_end = int(time.time()) - ripple_epoch
        # timeframe = 7776000  # 7776000 90 days  # 86400 5 days?
        # epoch_time_start = 1677038441 - ripple_epoch  # epoch_time_end - timeframe

        # go through all the messages
        async for message in message_iterator:
            # if should_stop:
            #     logger.info("Stopping processor")
            #     break

            # for all the process, collectors pair
            for pc in self.process_collectors_maps:

                output_messages = await retry_wrapper.aretry(
                    message,
                    pc.processor.aprocess,
                )

                if type(output_messages) != list:
                    raise ValueError(
                        "output message from processor" +
                        "must be a list but got '%s'" % type(output_messages))

                # run through the collectors for the corresponding
                # Collectors
                for m in output_messages:
                    # if type(m) is dict:
                        #  message_dict = dict(m)
                        # if message_dict.get("ledger") is not None and dict(message_dict.get("ledger")).get("close_time") is not None:
                        #     logger.warning("start time: " + str(epoch_time_start) + " current ledger time " + str(m.get("ledger").get("close_time")))
                        #     if epoch_time_start > m.get("ledger").get("close_time"):
                        #         should_stop = True
                        #         logger.warning("stopping processors since start time " + str(epoch_time_start) + " is greater than ledger time " + str(m.get("ledger").get("close_time")))

                    for c in pc.collectors:
                        await c.acollect_output(m)

                # if there is an output collector
                # collect the output as a whole
                # if self.output_collector:
                #     await self.output_collector.acollect(
                #         input = message,
                #         output = output_messages,
                #     )
