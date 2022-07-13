from ekspiper.datasource.xrpledger import LedgerCreationDataSource
import unittest

class LedgerCreationDataSourceTest(unittest.IsolatedAsyncioTestCase):

    async def test_good(self):
        ledger_creation_itr = LedgerCreationDataSource()
        ledger_creation_itr.start()

        async for value in ledger_creation_itr: 
            ledger_creation_itr.stop()
            self.assertTrue(value.get("result"))