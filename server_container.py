import argparse
import asyncio
import logging
import signal
import sys
from functools import partial

import yaml
from aiohttp import web, web_app
from fluent.asyncsender import FluentSender
from xrpl.asyncio.clients import AsyncJsonRpcClient

from ekspiper.builder.flow import (
    ProcessCollectorsMapBuilder,
    TemplateFlowBuilder,
)
from ekspiper.connect.queue import QueueSourceSink
from ekspiper.connect.xrpledger import LedgerCreationDataSource
from ekspiper.processor.etl import (
    ETLTemplateProcessor,
    GenericValidator,
    XRPLGenericTransformer,
)
from ekspiper.processor.fetch_transactions import (
    XRPLFetchLedgerDetailsProcessor,
    XRPLExtractTransactionsFromLedgerProcessor, XRPLLedgerProcessor, LedgerIndexProcessor,
)
from ekspiper.schema.xrp import XRPLTransactionSchema, XRPLLedgerSchema
from ekspiper.util.endpoints import endpoints, wss_endpoints

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)


async def health_check(request):
    return web.Response(text="healthy")


def load_from_file(
        yml_path: str,
):
    logger.info("[ServerContainer] loading config from path: " + yml_path)
    try:
        with open(yml_path, mode="rt", encoding="utf-8") as file:
            yml_config = yaml.safe_load(file)
            logger.info("[ServerContainer] config file: " + str(yml_config))
    except Exception as e:
        logger.info("[ServerContainer] Wasn't able to load config file: " + str(e))

    return yml_config


async def stop_template_flows(
        app: web_app.Application,
):
    print("Stopping the web application....")
    on_exit()
    # theoretically, if we stop the sources, flow should
    # drain out and exit gracefully
    app["ledger_creation_source"].stop()
    # app["book_offers_fetch_flow_source_sink"].stop()
    # app["book_offers_req_flow_source_sink"].stop()
    app["ledger_record_source_sink"].stop()
    app["txn_record_source_sink"].stop()

    await app["ledger_creation_source_task"]

    # now wait for them to drain
    await app["flow_ledger_details"]
    # await app["flow_booker_offers_fetch"]
    # for r in app["flow_booker_offer_records"]:
    #     await r
    await app["flow_txn_record"]
    await app["flow_ledger_record"]
    await app["flow_ledger_to_txns_brk"]


async def websocket_supervisor(ledger_creation_source):
    while True:
        try:
            logger.warning("Attempting to connect to server...")
            await ledger_creation_source.start()
        except Exception as e:
            logger.warning("There was an error starting the ledger creation source: " + str(e))

        await asyncio.sleep(5)


def on_exit():
    logger.info("Exiting...")
    try:
        if app["ledger_creation_source"].last_ledger is not None:
            with open(app.ledger_index_file_path, "a+") as f:
                if type(app["ledger_creation_source"].last_ledger) is not str:
                    raise Exception("ledger had wrong type: " + str(type(app["ledger_creation_source"].last_ledger)))
                f.write(app["ledger_creation_source"].last_ledger)
                logger.info("Writing ledger to file: " + str(app["ledger_creation_source"].last_ledger))
    except Exception as e:
        logger.error("Failed to write to file: " + str(e))

    sys.exit(0)


async def start_template_flows(
        app: web_app.Application,
        fluent_tag: str = None,
        fluent_host: str = "fluent-bit",
        fluent_port: int = 25225,
):
    if fluent_tag not in endpoints:
        raise RuntimeError(
            "[ExtractXRPLTransactions] Could not recognize fluent tag - did you forget to specify the fluent tag? " +
            str(fluent_tag))

    xrpl_endpoint = endpoints[fluent_tag]
    wss_endpoint = wss_endpoints[fluent_tag]
    logger.info("[ExtractXRPLTransactions] using fluent tag: " + fluent_tag)
    logger.info("[ExtractXRPLTransactions] using endpoint: " + xrpl_endpoint)
    logger.info("[ExtractXRPLTransactions] using WSS endpoint: " + wss_endpoint)

    async_rpc_client = AsyncJsonRpcClient(xrpl_endpoint)
    fluent_sender = FluentSender(fluent_tag + ".transactions", host=fluent_host, port=fluent_port)
    ledger_creation_source = LedgerCreationDataSource(wss_url=wss_endpoint)
    ledger_record_source_sink = QueueSourceSink(name="ledger_record_source_sink")
    txn_record_source_sink = QueueSourceSink(name="txn_record_source_sink")
    formatted_ledger_source_sink = QueueSourceSink(name="ledger_source_sink")
    app["ledger_creation_source_task"] = asyncio.create_task(websocket_supervisor(ledger_creation_source))
    app["ledger_creation_source"] = ledger_creation_source
    app["ledger_record_source_sink"] = ledger_record_source_sink
    app["txn_record_source_sink"] = txn_record_source_sink
    app["flow_ledger_details"] = []
    starting_index = None

    try:
        with open(app.ledger_index_file_path, "r") as f:
            logger.info("Reading ledger index from file")
            for line in f:
                starting_index = int(line)
    except FileNotFoundError:
        logger.info("No ledger index file present")

    if starting_index is not None:
        logger.info("Starting index: " + str(starting_index))

        current_index = await ledger_creation_source.async_queue.get()
        i = starting_index

        while i <= current_index:
            logger.info("Appending index to queue: " + str(i))
            ledger_creation_source.async_queue.put_nowait(i)
            i += 1

    ledger_index_processor = LedgerIndexProcessor(index_file_path=ledger_index_file_path)
    # create 10 tasks of the same to increase throughput
    for i in range(10):
        ledger_details_pc_map_builder = ProcessCollectorsMapBuilder()
        pc_map = ledger_details_pc_map_builder.with_processor(
            XRPLFetchLedgerDetailsProcessor(
                rpc_client=async_rpc_client,
                ledger_index_processor=ledger_index_processor,
            )
        ).add_data_sink_output_collector(
            data_sink=ledger_record_source_sink,
            name="ledger_record_source_sink",
        ).build()
        flow_ledger_details = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
        app["flow_ledger_details"].append(asyncio.create_task(flow_ledger_details.aexecute(
            message_iterator=ledger_creation_source,
        )))

    # Flow: Ledger to Transactions Break Flow
    pc_map = ProcessCollectorsMapBuilder().with_processor(
        XRPLExtractTransactionsFromLedgerProcessor(
            is_include_ledger_index=True,
        )
    ).add_data_sink_output_collector(
        data_sink=txn_record_source_sink,
        name="txn_record_source_sink",
    ).build()

    ledger_record_pc_map = ProcessCollectorsMapBuilder().with_processor(
        XRPLLedgerProcessor()
    ).add_data_sink_output_collector(
        data_sink=formatted_ledger_source_sink,
        name="txn_record_source_sink",
    ).build()

    flow_ledger_to_txns_brk = TemplateFlowBuilder().add_process_collectors_map(pc_map).add_process_collectors_map(
        ledger_record_pc_map).build()
    app["flow_ledger_to_txns_brk"] = asyncio.create_task(flow_ledger_to_txns_brk.aexecute(
        message_iterator=ledger_record_source_sink,
    ))

    # Flow: Transaction Record
    pc_map = ProcessCollectorsMapBuilder().with_processor(
        ETLTemplateProcessor(
            validator=GenericValidator(XRPLTransactionSchema.SCHEMA),
            transformer=XRPLGenericTransformer(XRPLTransactionSchema.SCHEMA),
        )
    ).with_stdout_output_collector(
        tag_name=fluent_tag,
        is_simplified=True
    ).add_fluent_output_collector(
        fluent_sender=fluent_sender,
    ).build()
    flow_txn_record = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    app["flow_txn_record"] = asyncio.create_task(flow_txn_record.aexecute(
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
    logger.info("done building, running...")
    app["flow_ledger_record"] = asyncio.create_task(flow_ledger_record.aexecute(
        message_iterator=formatted_ledger_source_sink,
    ))


def parse_arguments() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument(
        "-ft",
        "--fluent_tag",
        help="specify the name to tag the FluentD/Bit entries",
        type=str,
        default=None,  # use prod for forwarding to GCP
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
        "-c",
        "--config",
        help="specify the configuration file",
        type=str,
        default="/tmp/config.yml",
    )

    return arg_parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    config = load_from_file(args.config)
    fluent_tag = config["network"] if "network" in config and config["network"] is not None else args.fluent_tag
    ledger_index_file_path = config["ledger_index_path"] if "ledger_index_path" in config else "/app/persistent_data/ledgers.txt"

    app = web.Application()
    app.add_routes([
        web.get('/', handle),
        web.get('/{name}', handle),
        web.get('/health', health_check),
    ])
    app.ledger_index_file_path = ledger_index_file_path

    app.on_startup.append(partial(start_template_flows, fluent_tag=fluent_tag))
    app.on_cleanup.append(stop_template_flows)
    app.on_shutdown.append(stop_template_flows)

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, on_exit)
    loop.add_signal_handler(signal.SIGTERM, on_exit)

    web.run_app(app, loop=loop)

