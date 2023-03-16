import argparse
import asyncio
import queue
from logging.handlers import QueueHandler, QueueListener

from ekspiper.builder.flow import (
    ProcessCollectorsMapBuilder,
    TemplateFlowBuilder,
)
from fluent.asyncsender import FluentSender
from ekspiper.connect.counter import PartitionedCounterDataSource
from ekspiper.connect.file_data_source import FileDataSource
from ekspiper.connect.queue import QueueSourceSink
from ekspiper.processor.fetch_transactions import (
    XRPLFetchLedgerDetailsProcessor,
    XRPLExtractTransactionsFromLedgerProcessor,
    PaymentTransactionSummaryProcessor,
)
from ekspiper.processor.etl import (
    ETLTemplateProcessor,
    GenericValidator,
    XRPLTransactionTransformer,
)
from ekspiper.schema.xrp import XRPLTransactionSchema, XRPLTestnetSchema
from ekspiper.metric.prom import ScriptExecutionMetrics
import logging
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.asyncio.ledger import get_latest_validated_ledger_sequence
from prometheus_client import (
    CollectorRegistry,
    generate_latest,
    push_to_gateway,
)


logger = logging.getLogger(__name__)
log_queue = queue.Queue(-1)
queue_handler = QueueHandler(log_queue)
logger.addHandler(queue_handler)
listener = QueueListener(log_queue)
listener.start()
#logging.basicConfig(level=logging.INFO)


async def start_ledger_sequence(client) -> int:
    return await get_latest_validated_ledger_sequence(client) - 1


async def amain_file(
        file: str = None,
        xrpl_endpoint: str = "https://s2.ripple.com:51234",
        fluent_tag: str = "test",
        fluent_host: str = "0.0.0.0",
        fluent_port: int = 25225,
        schema: str = "devnet",
):
    file_data_source = FileDataSource(
        file = file,
    )

    file_data_source.start()
    async_rpc_client = AsyncJsonRpcClient(xrpl_endpoint)
    ledger_record_source_sink = QueueSourceSink(
        name = "ledger_record_source",
    )
    pc_map = ProcessCollectorsMapBuilder().with_processor(
        XRPLFetchLedgerDetailsProcessor(
            rpc_client = async_rpc_client,
        )
    ).add_data_sink_output_collector(
        data_sink = ledger_record_source_sink,
        name = "ledger_record_source_sink"
    ).build()

    flow_payment_detail = TemplateFlowBuilder().add_process_collectors_map(
        pc_map
    ).build()
    flow_ledger_detail_tasks = [asyncio.create_task(flow_payment_detail.aexecute(
        message_iterator=file_data_source
    ))]
    txn_record_source_sink = QueueSourceSink(
        name = "txn_record_source_sink",
    )

    # Flow: Break down the ledger into transactions
    #
    pc_map = ProcessCollectorsMapBuilder().with_processor(
        XRPLExtractTransactionsFromLedgerProcessor(
            is_include_ledger_index = True,
        )
    ).add_data_sink_output_collector(
        data_sink = txn_record_source_sink,
        name = "txn_record_source_sink"
    ).build()

    flow_ledger_to_txns_brk = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_ledger_to_txns_brk_task = asyncio.create_task(flow_ledger_to_txns_brk.aexecute(
        message_iterator = ledger_record_source_sink,
    ))

    # setup fluent client
    fluent_sender = FluentSender(
        fluent_tag,
        host = fluent_host,
        port = fluent_port,
    )

    # Flow: Transaction Record
    #
    schemaToUse = XRPLTransactionSchema.SCHEMA
    if schema == "testnet":
        schemaToUse = XRPLTestnetSchema.SCHEMA

    logger.warning("Using schema: ", schemaToUse)

    txn_rec_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = txn_rec_pc_map_builder.with_processor(
        ETLTemplateProcessor(
            validator = GenericValidator(schemaToUse),
            transformer = XRPLTransactionTransformer(schemaToUse),
        )
    ).with_stdout_output_collector(
        tag_name = "transactions",
        is_simplified = False
    ).add_bigquery_output_collector(
        project='ripplex-347905',
        dataset='testnet_transaction_data',
        table='xrpl_transactions_testnet'
    ).add_fluent_output_collector(
        tag_name="ledger_txn",
        fluent_sender=fluent_sender
    ).build()
    flow_txn_record = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_txn_record_task = asyncio.create_task(flow_txn_record.aexecute(
        message_iterator = txn_record_source_sink,
    ))

    await flow_txn_record_task

    listener.stop()


async def amain(
    xrpl_endpoint: str = "https://s2.ripple.com:51234",
    fluent_tag: str = "test",
    fluent_host: str = "0.0.0.0",
    fluent_port: int = 25225,
    schema: str = "devnet",
):
    async_rpc_client = AsyncJsonRpcClient(xrpl_endpoint)
    start_index = await start_ledger_sequence(async_rpc_client)

    # build the ledger queue for processing
    ledger_record_source_sink = QueueSourceSink(
        name = "ledger_record_source",
    )

    # Flow: Obtain Ledger Details
    #
    flow_ledger_detail_tasks = []
    partition_size = 100
    for i in range(partition_size):
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
        ).add_data_sink_output_collector(
            data_sink = ledger_record_source_sink,
            name = "ledger_record_source_sink"
        ).build()

        flow_payment_detail = TemplateFlowBuilder().add_process_collectors_map(
            pc_map
        ).build()

        flow_ledger_detail_tasks.append(asyncio.create_task(flow_payment_detail.aexecute(
            message_iterator = index_decrementor_data_source
        )))

    # build the transaction queue for processing
    txn_record_source_sink = QueueSourceSink(
        name = "txn_record_source_sink",
    )

    # Flow: Break down the ledger into transactions
    #
    pc_map = ProcessCollectorsMapBuilder().with_processor(
        XRPLExtractTransactionsFromLedgerProcessor(
            is_include_ledger_index = True,
        )
    ).add_data_sink_output_collector(
        data_sink = txn_record_source_sink,
        name = "txn_record_source_sink"
    ).build()

    flow_ledger_to_txns_brk = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_ledger_to_txns_brk_task = asyncio.create_task(flow_ledger_to_txns_brk.aexecute(
        message_iterator = ledger_record_source_sink,
    ))

    # setup fluent client
    fluent_sender = FluentSender(
        fluent_tag,
        host = fluent_host,
        port = fluent_port,
    )

    # Flow: Transaction Record
    #
    schemaToUse = XRPLTransactionSchema.SCHEMA
    if schema == "testnet":
        schemaToUse = XRPLTestnetSchema.SCHEMA

    logger.warning("Using schema: ", schemaToUse)

    txn_rec_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = txn_rec_pc_map_builder.with_processor(
        ETLTemplateProcessor(
            validator = GenericValidator(schemaToUse),
            transformer = XRPLTransactionTransformer(schemaToUse),
        )
    ).with_stdout_output_collector(
        tag_name = "transactions",
        is_simplified = True
    ).add_fluent_output_collector(
        tag_name="ledger_txn",
        fluent_sender=fluent_sender
    ).build()
    # TODO: Enable when fluent is ready
    #).add_fluent_output_collector(
    #    tag_name = "ledger_txn",
    #    fluent_sender = fluent_sender,
    #).build()
    flow_txn_record = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_txn_record_task = asyncio.create_task(flow_txn_record.aexecute(
        message_iterator = txn_record_source_sink,
    ))

    # TODO: for now
    #asyncio.gather(*flow_ledger_detail_tasks)
    await flow_txn_record_task

    listener.stop()


def parse_arguments() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument(
        "-ft",
        "--fluent_tag",
        help = "specify the name to tag the FluentD/Bit entries",
        type = str,
        default = "test", # use prod for forwarding to GCP
    )
    arg_parser.add_argument(
        "-fh",
        "--fluent_host",
        help = "specify the FluentD/Bit host",
        type = str,
        default = "0.0.0.0",
    )
    arg_parser.add_argument(
        "-fp",
        "--fluent_port",
        help = "specify the FluentD/Bit port",
        type = int,
        default = 25225,
    )
    arg_parser.add_argument(
        "-x",
        "--xrpl_endpoint",
        help = "specify the rippled RESTful API endpoint",
        type = str,
        default = "https://s2.ripple.com:51234",
    )
    arg_parser.add_argument(
        "-s",
        "--schema",
        help = "specify the schema to use",
        type = str,
        default = "devnet",
    )

    arg_parser.add_argument(
        "-f",
        "--file",
        help = "get ledgers from file",
        type = str,
        default = None,
    )

    return arg_parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    registry = CollectorRegistry()

    with ScriptExecutionMetrics(
        prom_registry = registry,
        job_name = "extract_ledger_txns",
    ):
        logger.warning("running other main")
        if args.file is None:
            asyncio.run(amain(
                xrpl_endpoint = args.xrpl_endpoint,
                fluent_tag = args.fluent_tag,
                fluent_host = args.fluent_host,
                fluent_port = args.fluent_port,
                schema = args.schema,
            ))
        else:
            asyncio.run(amain_file(
                file = args.file,
                xrpl_endpoint = args.xrpl_endpoint,
                fluent_tag = args.fluent_tag,
                fluent_host = args.fluent_host,
                fluent_port = args.fluent_port,
                schema = args.schema,
            ))

    print(generate_latest(registry))

    # previous method
    asyncio.run(amain())
