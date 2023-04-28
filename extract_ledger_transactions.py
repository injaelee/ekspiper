import argparse
import asyncio
import logging
import queue
from logging.handlers import QueueHandler, QueueListener

import xrpl
from fluent.asyncsender import FluentSender
from prometheus_client import (
    CollectorRegistry,
    generate_latest,
)
from xrpl.asyncio.clients import AsyncJsonRpcClient

import ekspiper.util.xrplpy_patches
from ekspiper.builder.flow import (
    ProcessCollectorsMapBuilder,
    TemplateFlowBuilder,
)
from ekspiper.connect.counter import PartitionedCounterDataSource
from ekspiper.connect.file_data_source import FileDataSource
from ekspiper.connect.queue import QueueSourceSink
from ekspiper.metric.prom import ScriptExecutionMetrics
from ekspiper.processor.etl import (
    ETLTemplateProcessor,
    GenericValidator,
    XRPLGenericTransformer,
)
from ekspiper.processor.fetch_transactions import (
    XRPLFetchLedgerDetailsProcessor,
    XRPLExtractTransactionsFromLedgerProcessor, XRPLLedgerProcessor,
)
from ekspiper.schema.xrp import XRPLTransactionSchema, XRPLObjectSchema, XRPLLedgerSchema
from ekspiper.util import endpoints
from ekspiper.util.xrplpy_patches import get_latest_validated_ledger_sequence

# TODO: remove monkey patch when clio release is done: https://ripplelabs.atlassian.net/browse/CLIO-260
xrpl.models.Ledger = ekspiper.util.xrplpy_patches.Ledger
logger = logging.getLogger(__name__)
log_queue = queue.Queue(-1)
queue_handler = QueueHandler(log_queue)
logger.addHandler(queue_handler)
listener = QueueListener(log_queue)
listener.start()


# logging.basicConfig(level=logging.INFO)


async def start_ledger_sequence(client) -> int:
    return await get_latest_validated_ledger_sequence(client) - 1


async def amain_file(
        file: str = None,
        fluent_tag: str = "test",
        fluent_host: str = "0.0.0.0",
        fluent_port: int = 25225,
        schema: str = "transaction",
):
    xrpl_endpoint = endpoints[fluent_tag]
    if xrpl_endpoint is None:
        raise RuntimeError(
            "[ExtractXRPLTransactions] missing xrpl endpoint - did you forget to specify the fluent tag?")
    file_data_source = FileDataSource(file=file)
    file_data_source.start()
    async_rpc_client = AsyncJsonRpcClient(xrpl_endpoint)
    ledger_record_source_sink = QueueSourceSink(
        name="ledger_record_source",
    )
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
    flow_ledger_detail_tasks = [asyncio.create_task(flow_payment_detail.aexecute(
        message_iterator=file_data_source
    ))]
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

    # setup fluent client
    fluent_sender = FluentSender(
        fluent_tag,
        host=fluent_host,
        port=fluent_port,
    )

    # Flow: Transaction Record
    #
    schema_to_use = XRPLTransactionSchema.SCHEMA
    if schema == "object":
        schema_to_use = XRPLObjectSchema.SCHEMA

    logger.warning("Using schema: ", schema)

    txn_rec_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = txn_rec_pc_map_builder.with_processor(
        ETLTemplateProcessor(
            validator=GenericValidator(schema_to_use),
            transformer=XRPLGenericTransformer(schema_to_use),
        )
    ).with_stdout_output_collector(
        tag_name="transactions",
        is_simplified=False
    ).add_bigquery_output_collector(
        project='ripplex-347905',
        dataset='testnet',
        table='transactions'
    ).build()
    # ).add_fluent_output_collector(
    #     tag_name="ledger_txn",
    #     fluent_sender=fluent_sender
    # ).build()
    flow_txn_record = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_txn_record_task = asyncio.create_task(flow_txn_record.aexecute(
        message_iterator=txn_record_source_sink,
    ))

    await flow_txn_record_task

    listener.stop()


async def amain(
        fluent_tag: str = "mainnet",
        fluent_host: str = "0.0.0.0",
        fluent_port: int = 25225,
):
    xrpl_endpoint = endpoints[fluent_tag]
    if xrpl_endpoint is None:
        raise RuntimeError(
            "[ExtractXRPLTransactions] missing xrpl endpoint - did you forget to specify the fluent tag?")
    async_rpc_client = AsyncJsonRpcClient(xrpl_endpoint)
    start_index = await start_ledger_sequence(async_rpc_client)

    # build the ledger queue for processing
    ledger_record_source_sink = QueueSourceSink(name="ledger_record_source")

    # Flow: Obtain Ledger Details
    #
    flow_ledger_detail_tasks = []
    partition_size = 100
    for i in range(partition_size):
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

        flow_payment_detail = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
        flow_ledger_detail_tasks.append(asyncio.create_task(flow_payment_detail.aexecute(
            message_iterator=index_decrementor_data_source
        )))

    # build the transaction queue for processing
    txn_record_source_sink = QueueSourceSink(name="txn_record_source_sink")
    formatted_ledger_source_sink = QueueSourceSink(name="formatted_ledger_source_sink")

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

    ledger_record_pc_map = ProcessCollectorsMapBuilder().with_processor(
        XRPLLedgerProcessor()
    ).add_data_sink_output_collector(
        data_sink=formatted_ledger_source_sink,
        name="ledger_record_source_sink",
    ).build()

    flow_ledger_to_txns_brk = TemplateFlowBuilder().add_process_collectors_map(pc_map).add_process_collectors_map(
        ledger_record_pc_map).build()
    flow_ledger_to_txns_brk_task = asyncio.create_task(flow_ledger_to_txns_brk.aexecute(
        message_iterator=ledger_record_source_sink,
    ))

    pc_map_transaction = ProcessCollectorsMapBuilder().with_processor(
        ETLTemplateProcessor(
            validator=GenericValidator(XRPLTransactionSchema.SCHEMA),
            transformer=XRPLGenericTransformer(XRPLTransactionSchema.SCHEMA),
        )
    ).with_stdout_output_collector(
        is_simplified=True
    ).add_fluent_output_collector(
        fluent_sender=FluentSender(fluent_tag + ".transactions", host=fluent_host, port=fluent_port)
    ).build()

    flow_txn_record = TemplateFlowBuilder().add_process_collectors_map(pc_map_transaction).build()
    flow_txn_record_task = asyncio.create_task(flow_txn_record.aexecute(
        message_iterator=txn_record_source_sink,
    ))

    pc_map_ledgers = ProcessCollectorsMapBuilder().with_processor(
        ETLTemplateProcessor(
            validator=GenericValidator(XRPLLedgerSchema.SCHEMA),
            transformer=XRPLGenericTransformer(XRPLLedgerSchema.SCHEMA),
        )
    ).with_stdout_output_collector(
        tag_name=fluent_tag,
        is_simplified=True
    ).add_fluent_output_collector(
        fluent_sender=FluentSender(fluent_tag + ".ledgers", host=fluent_host, port=fluent_port),
    ).build()
    flow_ledger_record = TemplateFlowBuilder().add_process_collectors_map(pc_map_ledgers).build()
    flow_ledger_record_task = asyncio.create_task(flow_ledger_record.aexecute(
        message_iterator=formatted_ledger_source_sink,
    ))

    # TODO: for now
    await asyncio.gather(flow_ledger_record_task, flow_txn_record_task)
    # await flow_txn_record_task

    listener.stop()


def parse_arguments() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument(
        "-ft",
        "--fluent_tag",
        help="specify the name to tag the FluentD/Bit entries",
        type=str,
        default="test",  # use prod for forwarding to GCP
    )
    arg_parser.add_argument(
        "-fh",
        "--fluent_host",
        help="specify the FluentD/Bit host",
        type=str,
        default="0.0.0.0",
    )
    arg_parser.add_argument(
        "-fp",
        "--fluent_port",
        help="specify the FluentD/Bit port",
        type=int,
        default=25225,
    )

    arg_parser.add_argument(
        "-f",
        "--file",
        help="get ledgers from file",
        type=str,
        default=None,
    )

    return arg_parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    registry = CollectorRegistry()

    with ScriptExecutionMetrics(
            prom_registry=registry,
            job_name="extract_ledger_txns",
    ):
        logger.warning("running other main")
        if args.file is None:
            asyncio.run(amain(
                fluent_tag=args.fluent_tag,
                fluent_host=args.fluent_host,
                fluent_port=args.fluent_port,
            ))
        else:
            asyncio.run(amain_file(
                file=args.file,
                fluent_tag=args.fluent_tag,
                fluent_host=args.fluent_host,
                fluent_port=args.fluent_port,
                schema=args.schema,
            ))

    print(generate_latest(registry))

    # previous method
    asyncio.run(amain())
