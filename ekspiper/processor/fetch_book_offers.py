from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models.requests.book_offers import BookOffers
from xrpl.models.currencies import XRP, IssuedCurrency
from ekspiper.processor.base import EntryProcessor
from typing import Any, Dict, List, Union
import logging


logger = logging.getLogger(__name__)


class XRPLFetchBookOffersProcessor(EntryProcessor):
    def __init__(self,
        rpc_client: AsyncJsonRpcClient,
    ):
        # more than efficient for a request-response query pattern
        #  - server is not pushing any information; must have a request
        #  - make sure HTTP keep-alive to avoid reconnect/establishment
        self.rpc_client = rpc_client

    async def aprocess(self,
        entry: BookOffers,
    ) -> List[Dict[str, Any]]:
        """
        Presume the entry is the BookOffers
        """
        if type(entry) != BookOffers:
            raise ValueError(
                "[XRPLFetchBookOffersProcessor] Expected 'BookOffers' but got '%s': %s" % (
                type(entry),
                entry,
            ))

        logger.info(
            "[XRPLFetchBookOffersProcessor] Fetching book offers: %s",
            entry,
        )

        response = await self.rpc_client.request(entry)

        # check the response success
        if not response.is_successful():
            raise ValueError("Error fetching book offers: %s" % entry)

        message = response.result

        """
        Reference:
          txns = message.get("ledger").get("transactions")
          ledger_index = message.get("ledger_index")
        """
        return [message]


class BuildBookOfferRequestsProcessor(EntryProcessor):
    
    def build_currency(self,
        value: Union[str,Dict],
    ) -> Union[XRP, IssuedCurrency]:
        if type(value) == str:
            return XRP()

        amt = IssuedCurrency(
            currency = value.get("currency"),
            issuer = value.get("issuer"),
        )

        if amt.currency is None or amt.issuer is None:
            return None

        return amt

    async def aprocess(self,
        entry: Dict[str, Any], # expect response.get("result")
    ) -> List[BookOffers]:

        # extract all the token pairs
        transactions = entry.get(
            "ledger", {}).get(
            "transactions", [])

        ledger_index = entry.get("ledger_index")

        # idempotancy: to remove duplicates 
        pair_tuple_set = set()

        for txn in transactions:

            for node in txn.get("metaData", {}).get("AffectedNodes", []):

                data_node = node.get("ModifiedNode") or node.get("CreatedNode")
                if not data_node:
                    continue

                logger.info("Ledger entry type: %s", data_node.get("LedgerEntryType"))
                if data_node.get("LedgerEntryType") != "Offer":
                    # skip non offer induced changes
                    continue

                fields = data_node.get("FinalFields") or data_node.get("NewFields")
                taker_gets = fields.get("TakerGets")
                taker_pays = fields.get("TakerPays")

                if not taker_gets or not taker_pays:
                    # no need to continue without those data
                    continue

                taker_gets_currency = self.build_currency(taker_gets)
                taker_pays_currency = self.build_currency(taker_pays)

                pair_tuple_set.add((
                    taker_gets_currency,
                    taker_pays_currency
                ))

        book_offers_requests: List[BookOffer] = []
        for taker_gets_currency, taker_pays_currency in pair_tuple_set:
                logger.info(
                    "[BuildBookOfferRequestsProcessor] Enqueue book offer request: [%s], [%s]",
                    taker_gets_currency,
                    taker_pays_currency,
                )

                book_offers_requests.append(BookOffers(
                    ledger_index = ledger_index,
                    taker_gets = taker_gets_currency,
                    taker_pays = taker_pays_currency,
                ))

        logger.info("[BuildBookOfferRequestsProcessor] Done iteration.")

        return book_offers_requests