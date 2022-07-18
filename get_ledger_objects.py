import asyncio
from xrpl.asyncio.ledger import get_latest_validated_ledger_sequence
from ekspiper.builder.flow import (
    ProcessCollectorsMapBuilder,
    TemplateFlowBuilder,
)
from ekspiper.datasource.xrpledger import LedgerObjectDataSource
from xrpl.asyncio.clients import AsyncJsonRpcClient
from ekspiper.processor.base import PassthruProcessor
from fluent.asyncsender import FluentSender
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def amain():
    async_rpc_client = AsyncJsonRpcClient("https://s2.ripple.com:51234/")
    ledger_index = await get_latest_validated_ledger_sequence(async_rpc_client) - 1

    # setup fluent client
    fluent_sender = FluentSender(
        "test",
        host = "0.0.0.0", 
        port = 25225,
    )

    # setup the ledger object data source
    ledger_object_data_source = LedgerObjectDataSource(
        rpc_client = async_rpc_client,
        ledger_index = ledger_index,
    )
    ledger_object_data_source.start()

    # Flow: Export the Ledger Objects
    #
    ledger_obj_export_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = ledger_obj_export_pc_map_builder.with_processor(
        PassthruProcessor()
    #).with_stdout_output_collector(tag_name = "ledger_obj", is_simplified = False).build()
    ).add_fluent_output_collector(
        fluent_sender = fluent_sender,
        tag_name = "ledger_obj",
    ).build()
    #).add_async_queue_output_collector(
    #    async_queue = txn_record_flow_q,
    #).build()

    flow_ledger_obj_export = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_task = asyncio.create_task(flow_ledger_obj_export.aexecute(
        message_iterator = ledger_object_data_source,
    ))

    # Flow: Fluent Export
    await asyncio.sleep(100)


if __name__ == "__main__":
    asyncio.run(amain())
