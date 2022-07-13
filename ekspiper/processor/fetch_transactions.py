from typing import Any, Dict, Generic, List, TypeVar, Union
from ekspiper.processor.base import EntryProcessor
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models.requests.ledger import Ledger
import logging


logger = logging.getLogger(__name__)


class XRPLFetchLedgerDetailsProcessor(EntryProcessor):

    def __init__(self,
        rpc_client: AsyncJsonRpcClient,
    ):
        # more than efficient for a request-response query pattern
        #  - server is not pushing any information; must have a request
        #  - make sure HTTP keep-alive to avoid reconnect/establishment
        self.rpc_client = rpc_client

    async def aprocess(self,
        entry: Union[int, dict], # ledger index
    ) -> List[Dict[str, Any]]:
        """
        Presume the entry is the ledger index (int).
        """
        if type(entry) not in [int, dict]:
            raise ValueError(
                "[FetchXRPLTransactionsProcessor] Expected 'int' but got '%s': %s" % (
                type(entry),
                entry,
            ))

        if type(entry) == int:
            ledger_index = entry
        elif type(entry) == dict:
            ledger_index = entry.get(
                "result", {}).get("ledger_index") or entry.get("ledger_index")
        
        if not ledger_index:
            raise ValueError(
                "[FetchXRPLTransactionsProcessor] missing ledger index: %s" % (
                entry,  
            ))            

        logger.info(
            "[FetchXRPLTransactionsProcessor] Fetching transactions for ledger '%d'",
            ledger_index,
        )

        # build the request
        req = Ledger(
            ledger_index = ledger_index,
            transactions = True,
            expand = True,
        )
        response = await self.rpc_client.request(req)

        # check the response success
        if not response.is_successful():
            raise ValueError("Fetching transactions for ledger '%d'" % ledger_index)

        message = response.result
        """
        Reference:
          txns = message.get("ledger").get("transactions")
          ledger_index = message.get("ledger_index")
        """
        return [message]