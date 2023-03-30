from ekspiper.processor.fetch_transactions import XRPLFetchLedgerDetailsProcessor
from xrpl.asyncio.clients import AsyncJsonRpcClient
import unittest

class FetchTest(unittest.IsolatedAsyncioTestCase):

    async def test_ledger_details_fetch(self):
        arpc_client = AsyncJsonRpcClient("https://s2.ripple.com:51234/")
        processor = XRPLFetchLedgerDetailsProcessor(
            rpc_client = arpc_client,
        )
        output = await processor.aprocess(entry = 72959850)
        
        txns = output[0].get("ledger").get("transactions")
        ledger_index = output[0].get("ledger_index")

        #import json; print(json.dumps(output, indent = "  "))

        self.assertEqual(int, type(ledger_index))
        self.assertTrue(len(txns) > 0)
