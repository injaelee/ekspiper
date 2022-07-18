from ekspiper.source.xrpledger import (
    LedgerCreationDataSource,
    LedgerObjectDataSource,
)
from xrpl.asyncio.clients import AsyncJsonRpcClient
import unittest

class LedgerCreationDataSourceTest(unittest.IsolatedAsyncioTestCase):

    async def test_good(self):
        ledger_creation_itr = LedgerCreationDataSource()
        ledger_creation_itr.start()

        async for value in ledger_creation_itr: 
            ledger_creation_itr.stop()
            self.assertTrue(value.get("result"))

    async def test_ledger_object(self):
        async_rpc_client = AsyncJsonRpcClient("https://s2.ripple.com:51234/")
        ledger_obj_itr = LedgerObjectDataSource(
            rpc_client = async_rpc_client,
        )
        ledger_obj_itr.start()
        
        entry_count = 0
        async for value in ledger_obj_itr:
            ledger_obj_itr.stop()

            entry_count += 1
            self.assertTrue(value.get("_LedgerIndex"))
            self.assertTrue(value.get("_ExecutionID"))
            self.assertTrue(value.get("_Sequence") >= 0)

        self.assertTrue(entry_count > 0)
