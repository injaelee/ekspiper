from typing import Dict, Any
import ekspiper
from xrpl.clients.json_rpc_client import JsonRpcClient
import logging


logger = logging.getLogger(__name__)


class FetchXRPLTransactionsProcessor(ekspiper.Processor):

	def __init__(self,
		rpc_client: JsonRpcClient,
	):
		self.rpc_client = rpc_client

	def process(self,
		entry: int, # ledger index
	) -> List[Dict[str, Any]]:

		response = client.request(req)

        if not response.is_successful():
            retry -= 1
            logger.error(f"[{itr_num}] Received message has failure. Sleeping.")
            time.sleep(10)
            continue

        message = response.result

        txns = message.get("ledger").get("transactions")
        ledger_index = message.get("ledger_index")

        return txns
