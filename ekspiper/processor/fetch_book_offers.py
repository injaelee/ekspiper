
from xrpl.models.requests.ledger import Ledger
from xrpl.models.requests.book_offers import BookOffers
from xrpl.models.currencies import XRP, IssuedCurrency

BookOfferRequest = collections.namedtuple(
    "BookOfferRequest",
    ["ledger_index", "taker_gets", "taker_pays"],
)

class FetchBookOfferProcessor(ekspiper.Processor):

	def process(self,
		entry: int, # ledger index
	) -> List[Dict[str, Any]]:
        book_offer_request = BookOffers(
            taker_gets = req.taker_gets,
            taker_pays = req.taker_pays,
            ledger_index = req.ledger_index,
        )

        await async_websocket_client.send(book_offer_request)


class ExtractTokenPairsAsyncProcessor(FetchAsyncProcessor):
    def __init__(self,
        aqueue: asyncio.Queue,
    ):
        self.aq = aqueue

    async def process(self,
        entry: Dict[str, Any],
    ):
        try:
            await self._process(entry)
        except Exception as exp:
            traceback.print_exc()

    async def _process(self,
        entry: Dict[str, Any],
    ):
        logger.info("[ExtractTokenPairsAsyncProcessor] Start iteration.")

        # extract all the token pairs
        transactions = entry.get(
            "result", {}).get(
            "ledger", {}).get(
            "transactions", [])

        ledger_index = entry.get("result", {}).get("ledger_index")

        def build_currency(
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

                taker_gets_currency = build_currency(taker_gets)
                taker_pays_currency = build_currency(taker_pays)

                pair_tuple_set.add((
                    taker_gets_currency,
                    taker_pays_currency
                ))

        for taker_gets_currency, taker_pays_currency in pair_tuple_set:
                logger.info(
                    "[ExtractTokenPairsAsyncProcessor] Enqueue book offer request: [%s], [%s]",
                    taker_gets_currency,
                    taker_pays_currency,
                )

                await self.aq.put(BookOfferRequest(
                    ledger_index = ledger_index,
                    taker_gets = taker_gets_currency,
                    taker_pays = taker_pays_currency,
                ))

        logger.info("[ExtractTokenPairsAsyncProcessor] Done iteration.")