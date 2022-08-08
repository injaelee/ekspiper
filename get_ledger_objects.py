import argparse
import asyncio
from xrpl.asyncio.ledger import get_latest_validated_ledger_sequence
from ekspiper.builder.flow import (
    ProcessCollectorsMapBuilder,
    TemplateFlowBuilder,
)
from ekspiper.connect.queue import QueueSourceSink
from ekspiper.connect.xrpledger import LedgerObjectDataSource
from xrpl.asyncio.clients import AsyncJsonRpcClient
from ekspiper.processor.base import PassthruProcessor
from ekspiper.processor.attribute import AttributeCollectionProcessor
from fluent.asyncsender import FluentSender
from ekspiper.schema.xrp import XRPLObjectSchema
from ekspiper.metric.prom import ScriptExecutionMetrics
import logging
from prometheus_client import (
    CollectorRegistry,
    generate_latest,
    push_to_gateway,
)


logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO)

"""
# TODO's
- [ ] Optionally specify specific ledger index

"""
async def amain(
    xrpl_endpoint: str = "https://s2.ripple.com:51234",
    fluent_host: str = "0.0.0.0",
    fluent_port: int = 25225,
):
    async_rpc_client = AsyncJsonRpcClient(xrpl_endpoint)
    ledger_index = await get_latest_validated_ledger_sequence(async_rpc_client) - 1

    # setup fluent client
    fluent_sender = FluentSender(
        "test",
        host = fluent_host,
        port = fluent_port,
    )

    # create the queues for output and schema check
    ledger_record_source_sink = QueueSourceSink(
        name = "ledger_record_source_sink",
    )
    def stop_data_source():
        ledger_record_source_sink.stop()

    # setup the ledger object data source
    ledger_object_data_source = LedgerObjectDataSource(
        rpc_client = async_rpc_client,
        ledger_index = ledger_index,
        done_callback = stop_data_source,
    )
    ledger_object_data_source.start()

    # Flow: Export the Ledger Objects
    #
    ledger_obj_export_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = ledger_obj_export_pc_map_builder.with_processor(
        PassthruProcessor()
    #).with_stdout_output_collector(tag_name = "ledger_obj", is_simplified = False
    ).add_data_sink_output_collector(
        data_sink = ledger_record_source_sink,
        name = "ledger_record_source_sink",
    ).add_fluent_output_collector(
        fluent_sender = fluent_sender,
        tag_name = "ledger_obj",
    ).build()

    flow_ledger_obj_export = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_ledger_obj_export_task = asyncio.create_task(flow_ledger_obj_export.aexecute(
        message_iterator = ledger_object_data_source,
    ))

    # Flow: Ledger Data Schema Attribute Collector
    pc_map = ProcessCollectorsMapBuilder().with_processor(
        AttributeCollectionProcessor(
            init_attribute_mapping = XRPLObjectSchema.SCHEMA,
        )
    ).with_stdout_output_collector(
        tag_name = "ledger_obj_schema",
    ).build()

    flow_ledger_data_schema = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_ledger_data_schema_task = asyncio.create_task(flow_ledger_data_schema.aexecute(
        message_iterator = ledger_record_source_sink
    ))

    # wait until all are done
    await asyncio.gather(
        flow_ledger_obj_export_task,
        flow_ledger_data_schema_task,
    )

    logger.info("[get_ledger_objects] completed run.")


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

    return arg_parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    registry = CollectorRegistry()

    with ScriptExecutionMetrics(
        prom_registry = registry,
        job_name = "get_ledger_objs",
    ):
        asyncio.run(amain(
            xrpl_endpoint = args.xrpl_endpoint,
            fluent_host = args.fluent_host,
            fluent_port = args.fluent_port,
        ))

    print(generate_latest(registry))
    #push_to_gateway('localhost:9091', job = 'batchA', registry = registry)
