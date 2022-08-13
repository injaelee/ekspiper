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


def parse_arguments() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser()

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
        job_name = "schema_collector",
    ):
        asyncio.run(amain(
            xrpl_endpoint = args.xrpl_endpoint,
        ))

    print(generate_latest(registry))