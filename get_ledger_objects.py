from xrpl.asyncio.ledger import get_latest_validated_ledger_sequence
import asyncio
import logging


logger = logging.getLogger(__name__)


async def amain():
    async_rpc_client = AsyncJsonRpcClient("https://s2.ripple.com:51234/")
    ledger_index = await get_latest_validated_ledger_sequence(async_rpc_client) - 1

    ledger_object_data_source = LedgerObjectDataSource(
        async_rpc_client = async_rpc_client,
        ledger_index = ledger_index,
    )



    ledger_to_txns_brk_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = ledger_to_txns_brk_pc_map_builder.with_processor(
        XRPLExtractTransactionsFromLedgerProcessor()
    #).with_stdout_output_collector(tag_name = "ledger_brk", is_simplified = True).build()
    ).add_async_queue_output_collector(
        async_queue = txn_record_flow_q,
    ).build()


    flow_ledger_obj_export = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_task = asyncio.create_task(flow_ledger_obj_export.aexecute(
        message_iterator = ledger_object_data_source,
    ))


if __name__ == "__main__":
    asyncio.run(amain())
