import unittest

from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models.currencies import XRP, IssuedCurrency
from xrpl.models.requests.book_offers import BookOffers

from ekspiper.processor.fetch_book_offers import XRPLFetchBookOffersProcessor


class BookOfferProcessorsTest(unittest.IsolatedAsyncioTestCase):

    async def test_fetch_book_offers(self):
        arpc_client = AsyncJsonRpcClient("https://s2.ripple.com:51234/")
        processor = XRPLFetchBookOffersProcessor(
            rpc_client=arpc_client,
        )
        book_offers_request = BookOffers(
            taker_gets=IssuedCurrency(
                currency='USD',
                issuer='rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B',
            ),
            taker_pays=XRP(),
            ledger_index=72959850,
        )
        output = await processor.aprocess(book_offers_request)
        # import json; print(json.dumps(output, indent = "  "))

        offers = output.get("offers")
        ledger_index = output.get("ledger_index")

        self.assertEqual(int, type(ledger_index))
        self.assertTrue(len(offers) > 0)
