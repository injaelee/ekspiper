import logging

logger = logging.getLogger(__name__)


class XRPLedgerObjectAppendDataProcessor:

    async def aprocess(self,
                       entry: Dict[str, Any],  # Ledger Object
                       ) -> List[Dict[str, Any]]:
        ledger_obj['_LedgerIndex'] = int(ledger_index)

        if self.is_attach_execution_id:
            ledger_obj['_ExecutionID'] = self.execution_id
