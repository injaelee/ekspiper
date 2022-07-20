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
    #).with_stdout_output_collector(tag_name = "ledger_obj", is_simplified = False).build()
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


if __name__ == "__main__":
    registry = CollectorRegistry()

    with ScriptExecutionMetrics(
        prom_registry = registry,
        job_name = "get_ledger_objs",
    ):
        asyncio.run(amain())

    print(generate_latest(registry))
    #push_to_gateway('localhost:9091', job = 'batchA', registry = registry)
