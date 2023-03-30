from ekspiper.template.processor import TemplateFlow, ProcessCollectorsMap
from ekspiper.processor.fetch_transactions import XRPLFetchLedgerDetailsProcessor
from ekspiper.collector.output import OutputCollector, STDOUTCollector
from ekspiper.connect.xrpledger import LedgerCreationDataSource
from xrpl.asyncio.clients import AsyncJsonRpcClient
import asyncio
import unittest
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TemplateFlowTest(unittest.IsolatedAsyncioTestCase):
    
    async def test_template_processor(self):
        arpc_client = AsyncJsonRpcClient("https://s2.ripple.com:51234/")
        
        output_collectors = [
            STDOUTCollector(),
        ]
        process_collectors_pairs = [
            ProcessCollectorsMap(
                processor = XRPLFetchLedgerDetailsProcessor(
                    rpc_client = arpc_client,
                ),
                collectors = output_collectors,
            )
        ]
        template_flow = TemplateFlow(
            process_collectors_maps = process_collectors_pairs
        )

        message_itr = LedgerCreationDataSource()
        message_itr.start()
        # stop immediately after 5 seconds to start the draining mode
        # so that we don't indefinitely wait
        await asyncio.sleep(5)        
        message_itr.stop()

        await template_flow.aexecute(
            message_iterator = message_itr,
        )
