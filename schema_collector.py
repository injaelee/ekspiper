import argparse
import asyncio
from xrpl.asyncio.ledger import get_latest_validated_ledger_sequence
from ekspiper.builder.flow import (
    ProcessCollectorsMapBuilder,
    TemplateFlowBuilder,
)
from ekspiper.connect.counter import PartitionedCounterDataSource
from ekspiper.connect.file_data_source import FileDataSource
from ekspiper.connect.queue import QueueSourceSink
from ekspiper.connect.xrpledger import LedgerObjectDataSource
from xrpl.asyncio.clients import AsyncJsonRpcClient
from ekspiper.processor.attribute import AttributeCollectionProcessor
from ekspiper.processor.base import PassthruProcessor
from ekspiper.processor.fetch_transactions import (
    XRPLFetchLedgerDetailsProcessor,
    XRPLExtractTransactionsFromLedgerProcessor,
)
from logging.handlers import QueueHandler, QueueListener

from fluent.asyncsender import FluentSender
from ekspiper.schema.xrp import (
    XRPLTransactionSchema,
    XRPLObjectSchema,
)
from ekspiper.metric.prom import ScriptExecutionMetrics
import logging
from prometheus_client import (
    CollectorRegistry,
    generate_latest,
    push_to_gateway,
)
import queue


logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO)
log_queue = queue.Queue(-1)
queue_handler = QueueHandler(log_queue)
logger.addHandler(queue_handler)
listener = QueueListener(log_queue)
listener.start()


"""
# TODO's
- [ ] Optionally specify specific ledger index

"""
async def amain(
    xrpl_endpoint: str = "https://s2.ripple.com:51234",
):
    async_rpc_client = AsyncJsonRpcClient(xrpl_endpoint)
    ledger_index = await get_latest_validated_ledger_sequence(async_rpc_client) - 1

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
        AttributeCollectionProcessor(
            init_attribute_mapping = XRPLObjectSchema.SCHEMA,
        )
    ).with_stdout_output_collector(
        tag_name = "ledger_obj_schema",
    ).build()

    flow_ledger_obj_export = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_ledger_obj_export_task = asyncio.create_task(flow_ledger_obj_export.aexecute(
        message_iterator = ledger_object_data_source,
    ))

    # wait until all are done
    await asyncio.gather(
        flow_ledger_obj_export_task,
    )

    logger.info("[get_ledger_objects] completed run.")


async def amain_txns_file(
        file: str,
        xrpl_endpoint: str = "https://s2.ripple.com:51234",
):
    async_rpc_client = AsyncJsonRpcClient(xrpl_endpoint)

    # setup the ledger object data source
    file_data_source = FileDataSource(file)
    file_data_source.start()

    # build the ledger queue for processing
    ledger_record_source_sink = QueueSourceSink(
        name = "ledger_record_source",
    )

    # Flow: Obtain Ledger Details
    #
    flow_ledger_detail_tasks = []
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
        message_iterator = file_data_source,
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

    # Flow: Export the Ledger Objects
    #
    ledger_obj_export_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = ledger_obj_export_pc_map_builder.with_processor(
        AttributeCollectionProcessor(
            init_attribute_mapping = XRPLTransactionSchema.SCHEMA,
        )
    ).with_stdout_output_collector(
        tag_name = "ledger_txn_schema",
    ).build()

    flow_ledger_obj_export = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_ledger_obj_export_task = asyncio.create_task(flow_ledger_obj_export.aexecute(
        message_iterator = txn_record_source_sink,
    ))

    # wait until all are done
    await asyncio.gather(
        flow_ledger_obj_export_task,
    )

    listener.stop()
    logger.info("[get_ledger_objects] completed run.")

async def start_ledger_sequence(client) -> int:
    return await get_latest_validated_ledger_sequence(client) - 1


async def amain_txns(
    xrpl_endpoint: str = "https://s2.ripple.com:51234",
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
        async_rpc_client = AsyncJsonRpcClient(xrpl_endpoint)

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
            message_iterator = index_decrementor_data_source,
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

    # Flow: Export the Ledger Objects
    #
    ledger_obj_export_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = ledger_obj_export_pc_map_builder.with_processor(
        AttributeCollectionProcessor(
            init_attribute_mapping = XRPLTransactionSchema.SCHEMA,
        )
    ).with_stdout_output_collector(
        tag_name = "ledger_txn_schema",
    ).build()

    flow_ledger_obj_export = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_ledger_obj_export_task = asyncio.create_task(flow_ledger_obj_export.aexecute(
        message_iterator = txn_record_source_sink,
    ))

    # wait until all are done
    await asyncio.gather(
        flow_ledger_obj_export_task,
    )

    listener.stop()
    logger.info("[get_ledger_objects] completed run.")


def parse_arguments() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument(
        "-x",
        "--xrpl_endpoint",
        help = "specify the rippled RESTful API endpoint",
        type = str,
        default = "https://s2.ripple.com:51234",
    )

    arg_parser.add_argument(
        "-f",
        "--file",
        help = "the file to read ledger indicies from",
        type = str,
        default = None,
    )

    arg_parser.add_argument(
        "-t",
        "--type",
        choices = ["ledger_obj", "ledger_txn"],
        help = "specify the data type",
        type = str,
        default = "ledger_obj",
    )

    return arg_parser.parse_args()

"""
# Output could be formatted with:
```
grep ledger_txn_schema o.schema.txns.testnet | grep 1676525104-27901104 | \
cut -f2,3 | sed "s/<class '//g" | sed "s/'>, /,/g" | sed "s/'>//g" | \
awk '{print "\""$1"\": " $2","}'
```
"""
if __name__ == "__main__":
    args = parse_arguments()
    registry = CollectorRegistry()

    with ScriptExecutionMetrics(
        prom_registry = registry,
        job_name = "schema_collector",
    ):
        if args.type == "ledger_obj":
            asyncio.run(amain(
                xrpl_endpoint = args.xrpl_endpoint,
            ))
        elif args.type == "ledger_txn":
            if args.file is not None:
                asyncio.run(amain_txns_file(
                    file = args.file,
                    xrpl_endpoint = args.xrpl_endpoint,
                ))
            else:
                asyncio.run(amain_txns(#amain(
                    xrpl_endpoint = args.xrpl_endpoint,
                ))
        else:
            raise ValueError("Unknown option data type '{}'".format(args.type))

    print(generate_latest(registry))