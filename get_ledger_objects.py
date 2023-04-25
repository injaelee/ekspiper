import argparse
import asyncio
import logging

from fluent.asyncsender import FluentSender
from prometheus_client import (
    CollectorRegistry,
    generate_latest,
)
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.asyncio.ledger import get_latest_validated_ledger_sequence

from ekspiper.builder.flow import (
    ProcessCollectorsMapBuilder,
    TemplateFlowBuilder,
)
from ekspiper.connect.xrpledger import LedgerObjectDataSource
from ekspiper.metric.prom import ScriptExecutionMetrics
from ekspiper.processor.etl import (
    ETLTemplateProcessor,
    GenericValidator,
    XRPLObjectTransformer,
)
from ekspiper.schema.xrp import XRPLObjectSchema

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def amain(
        xrpl_endpoint: str = "https://s2.ripple.com:51234",
        fluent_tag: str = "test",
        fluent_host: str = "0.0.0.0",
        fluent_port: int = 25225,
):
    """
    # TODO's
    - [ ] Optionally specify specific ledger index

    """
    async_rpc_client = AsyncJsonRpcClient(xrpl_endpoint)
    ledger_index = await get_latest_validated_ledger_sequence(async_rpc_client) - 1

    # setup fluent client
    fluent_sender = FluentSender(
        fluent_tag,
        host=fluent_host,
        port=fluent_port,
    )

    # setup the ledger object data source
    ledger_object_data_source = LedgerObjectDataSource(
        rpc_client=async_rpc_client,
        ledger_index=ledger_index,
    )
    ledger_object_data_source.start()

    # Flow: Export the Ledger Objects
    #
    ledger_obj_export_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = ledger_obj_export_pc_map_builder.with_processor(
        ETLTemplateProcessor(
            validator=GenericValidator(XRPLObjectSchema.SCHEMA),
            transformer=XRPLObjectTransformer(),
        )
    ).add_fluent_output_collector(
        fluent_sender=fluent_sender,
        tag_name="ledger_obj",
    ).build()

    flow_ledger_obj_export = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    flow_ledger_obj_export_task = asyncio.create_task(flow_ledger_obj_export.aexecute(
        message_iterator=ledger_object_data_source,
    ))

    # wait until all are done
    await asyncio.gather(
        flow_ledger_obj_export_task,
    )

    logger.info("[get_ledger_objects] completed run.")


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
        "-x",
        "--xrpl_endpoint",
        help="specify the rippled RESTful API endpoint",
        type=str,
        default="https://s2.ripple.com:51234",
    )

    return arg_parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    registry = CollectorRegistry()

    with ScriptExecutionMetrics(
            prom_registry=registry,
            job_name="get_ledger_objs",
    ):
        asyncio.run(amain(
            xrpl_endpoint=args.xrpl_endpoint,
            fluent_tag=args.fluent_tag,
            fluent_host=args.fluent_host,
            fluent_port=args.fluent_port,
        ))

    print(generate_latest(registry))
    # push_to_gateway('localhost:9091', job = 'batchA', registry = registry)
