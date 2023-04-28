import asyncio
import logging

from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.asyncio.ledger import get_latest_validated_ledger_sequence

from ekspiper.builder.flow import (
    ProcessCollectorsMapBuilder,
    TemplateFlowBuilder,
)
from ekspiper.connect.counter import PartitionedCounterDataSource
from ekspiper.connect.queue import QueueSourceSink
from ekspiper.processor.fetch_transactions import (
    XRPLFetchLedgerDetailsProcessor,
    XRPLExtractTransactionsFromLedgerProcessor,
    PaymentTransactionSummaryProcessor,
)

logger = logging.getLogger(__name__)


# logging.basicConfig(level=logging.INFO)


async def start_ledger_sequence(client) -> int:
    return await get_latest_validated_ledger_sequence(client) - 1


async def amain():
    async_rpc_client = AsyncJsonRpcClient("https://s2.ripple.com:51234/")
    start_index = await start_ledger_sequence(async_rpc_client)

    # build the ledger queue for processing
    ledger_record_source_sink = QueueSourceSink(
        name="ledger_record_source",
    )

    # Flow: Obtain Ledger Details
    #
    flow_ledger_detail_tasks = []
    partition_size = 10
    for i in range(partition_size):
        async_rpc_client = AsyncJsonRpcClient("https://s2.ripple.com:51234/")

        # start with the counter
        index_decrementor_data_source = PartitionedCounterDataSource(
            starting_count=start_index,
            shard_index=i,
            shard_size=partition_size,
        )
        index_decrementor_data_source.start()

        pc_map = ProcessCollectorsMapBuilder().with_processor(
            XRPLFetchLedgerDetailsProcessor(
                rpc_client=async_rpc_client,
            )
        ).add_data_sink_output_collector(
            data_sink=ledger_record_source_sink,
            name="ledger_record_source_sink"
        ).build()

        flow_payment_detail = TemplateFlowBuilder().add_process_collectors_map(
            pc_map
        ).build()

        flow_ledger_detail_tasks.append(asyncio.create_task(flow_payment_detail.aexecute(
            message_iterator=index_decrementor_data_source,
        )))

    # build the transaction queue for processing
    txn_record_source_sink = QueueSourceSink(
        name="txn_record_source_sink",
    )

    # Flow: Break down the ledger into transactions
    #
    pc_map = ProcessCollectorsMapBuilder().with_processor(
        XRPLExtractTransactionsFromLedgerProcessor(
            is_include_ledger_index=True,
        )
    ).add_data_sink_output_collector(
        data_sink=txn_record_source_sink,
        name="txn_record_source_sink"
    ).build()

    flow_ledger_to_txns_brk = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_ledger_to_txns_brk_task = asyncio.create_task(flow_ledger_to_txns_brk.aexecute(
        message_iterator=ledger_record_source_sink,
    ))

    # Flow: Summarize the Ledger Transactions
    #
    pc_map = ProcessCollectorsMapBuilder().with_processor(
        PaymentTransactionSummaryProcessor()
    ).with_stdout_output_collector(tag_name="summary_txns").build()

    flow_summary_txns = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_summary_txns_task = asyncio.create_task(flow_summary_txns.aexecute(
        message_iterator=txn_record_source_sink,
    ))

    # TODO: for now
    # asyncio.gather(*flow_ledger_detail_tasks)
    await flow_summary_txns_task


if __name__ == "__main__":
    asyncio.run(amain())
