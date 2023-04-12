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

        # TODO: input extraction should be done elsewhere; not its responsibility
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
            raise ValueError("Error fetching transactions for ledger '%d'" % ledger_index)

        message = response.result
        """
        Reference:
          txns = message.get("ledger").get("transactions")
          ledger_index = message.get("ledger_index")
        """
        return [message]


class XRPLExtractTransactionsFromLedgerProcessor(EntryProcessor):
    def __init__(self,
        is_include_ledger_index = True,
    ):
        self.is_include_ledger_index = is_include_ledger_index

    async def aprocess(self,
        entry: Dict[str, Any], # ledger response object
    ) -> List[Dict[str, Any]]:

        # expectation
        transactions = entry.get("ledger").get("transactions")
        if not transactions:
            logger.warning("[XRPLExtractTransactionsFromLedgerProcessor] No transactions were found")

        if self.is_include_ledger_index:
            ledger_index = entry.get("ledger").get("ledger_index")
            for txn in transactions:
                txn["_LedgerIndex"] = int(ledger_index)

        return transactions


class PaymentTransactionSummaryProcessor(EntryProcessor):
    #def process(self,
    #    entry: Dict[str, Any],
    #    **kwargs,
    #):
    def _parse_paths(self,
        paths: List[List[Dict[str,str]]],
    ) -> List[List[str]]:
        path_list = []
        for path in paths:
            resolved_path = []
            for step in path:
                currency = step.get("currency")
                issuer = step.get("issuer")
                account = step.get("account")

                if account:
                    cur = "rippling:" + account
                else:
                    cur = currency + ":" + issuer if issuer else currency

                resolved_path.append(cur)
            path_list.append(resolved_path)
        return path_list

    async def aprocess(self,
        entry: Dict[str, Any], # ledger response object
    ) -> List[Dict[str, Any]]:

        if entry.get("TransactionType") != "Payment":
            return []
        
        offer_count = 1
        path_size = 0

        step_sizes = []
        path_list = self._parse_paths(entry.get("Paths", []))
        path_size = len(path_list)
        paths_str = ""
        for steps in path_list:
            if paths_str:
                paths_str += "-"
            step_sizes.append(str(len(steps)))
            paths_str += ">".join(steps)

        for affected_node in entry.get("metaData", {}).get("AffectedNodes", []):
            if affected_node.get("ModifiedNode", {}).get("LedgerEntryType") == "Offer":
                offer_count += 1

        # obtain the transaction status
        txn_result = entry.get("metaData", {}).get("TransactionResult")

        ledger_index = entry.get("_LedgerIndex")
        txn_hash = entry.get("hash")

        step_sizes_str = "|" + "\t".join(step_sizes) if len(step_sizes) > 0 else ""
        return [f"{ledger_index}\t{txn_hash}\t{txn_result}\t{path_size}\t{offer_count}{step_sizes_str}\t*{paths_str}"]
