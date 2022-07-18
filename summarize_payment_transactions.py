import asyncio
import logging
from ekspiper.builder.flow import (
    ProcessCollectorsMapBuilder,
    TemplateFlowBuilder,
)
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.asyncio.ledger import get_latest_validated_ledger_sequence
from ekspiper.datasource.counter import PartitionedCounterDataSource
from ekspiper.processor.fetch_transactions import (
    XRPLFetchLedgerDetailsProcessor,
    XRPLExtractTransactionsFromLedgerProcessor,
    PaymentTransactionSummaryProcessor,
)
from ekspiper.datasource.queue import QueueSource


logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.INFO)


async def start_ledger_sequence(client) -> int:
    return await get_latest_validated_ledger_sequence(client) - 1


async def amain():
    async_rpc_client = AsyncJsonRpcClient("https://s2.ripple.com:51234/")
    start_index = await start_ledger_sequence(async_rpc_client)

    # build the ledger queue for processing
    ledger_record_flow_q = asyncio.Queue()
    ledger_record_source = QueueSource(
        name = "ledger_record_source",
        async_queue = ledger_record_flow_q,
    )

    # Flow: Obtain Ledger Details
    #
    flow_ledger_detail_tasks = []
    partition_size = 10
    for i in range(partition_size):
        async_rpc_client = AsyncJsonRpcClient("https://s2.ripple.com:51234/")
        
        # start with the counter
        index_decrementor_data_source = PartitionedCounterDataSource(
            starting_count = start_index,
            shard_index = i,
            shard_size = partition_size,
        )
        index_decrementor_data_source.start()
        
        pc_map = ProcessCollectorsMapBuilder().with_processor(
            XRPLFetchLedgerDetailsProcessor(
                rpc_client = async_rpc_client,
            )
        #).with_stdout_output_collector().build()
        ).add_async_queue_output_collector(
            async_queue = ledger_record_flow_q,
            name = "ledger_record_flow_q",
        ).build()

        flow_payment_detail = TemplateFlowBuilder().add_process_collectors_map(
            pc_map
        ).build()

        flow_ledger_detail_tasks.append(asyncio.create_task(flow_payment_detail.aexecute(
            message_iterator = index_decrementor_data_source,
        )))

    # build the transaction queue for processing
    transaction_record_flow_q = asyncio.Queue()
    transaction_record_source = QueueSource(
        name = "transaction_record_source",
        async_queue = transaction_record_flow_q,
    )

    # Flow: Break down the ledger into transactions
    #
    pc_map = ProcessCollectorsMapBuilder().with_processor(
        XRPLExtractTransactionsFromLedgerProcessor(
            is_include_ledger_index = True,
        )
    ).add_async_queue_output_collector(
        async_queue = transaction_record_flow_q,
        name = "transaction_record_flow_q",
    ).build()

    flow_ledger_to_txns_brk = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_ledger_to_txns_brk_task = asyncio.create_task(flow_ledger_to_txns_brk.aexecute(
        message_iterator = ledger_record_source,
    ))

    # Flow: Summarize the Ledger Transactions
    #
    pc_map = ProcessCollectorsMapBuilder().with_processor(
        PaymentTransactionSummaryProcessor()
    ).with_stdout_output_collector(tag_name = "summary_txns").build()

    flow_summary_txns = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_summary_txns_task = asyncio.create_task(flow_summary_txns.aexecute(
        message_iterator = transaction_record_source,
    ))

    # TODO: for now
    #asyncio.gather(*flow_ledger_detail_tasks)
    await flow_summary_txns_task

if __name__ == "__main__":
    asyncio.run(amain())