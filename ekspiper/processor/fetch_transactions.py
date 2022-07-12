from typing import Any, Dict, Generic, List, TypeVar
from ekspiper.processor.base import BaseProcessor
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models.requests.ledger import Ledger
import logging


logger = logging.getLogger(__name__)


class XRPLFetchLedgerDetailsProcessor(BaseProcessor):

    def __init__(self,
        rpc_client: AsyncJsonRpcClient,
    ):
        self.rpc_client = rpc_client

    async def aprocess(self,
        entry: int, # ledger index
    ) -> List[Dict[str, Any]]:
        """
        Presume the entry is the ledger index (int).
        """
        if type(entry) != int:
            raise ValueError(
                "[FetchXRPLTransactionsProcessor] Expected 'int' but got '%s': %s",
                type(entry),
                entry,
            )

        logger.info(
            "[FetchXRPLTransactionsProcessor] Fetching transactions for ledger '%d'",
            entry,
        )

        # build the request
        req = Ledger(
            ledger_index = entry,
            transactions = True,
            expand = True,
        )
        response = await self.rpc_client.request(req)

        # check the response success
        if not response.is_successful():
            raise ValueError("Fetching transactions for ledger '%d'" % entry)

        message = response.result
        """
        Reference:
          txns = message.get("ledger").get("transactions")
          ledger_index = message.get("ledger_index")
        """
        return message