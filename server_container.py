import argparse

from aiohttp import web, web_app
import asyncio
from ekspiper.builder.flow import (
    ProcessCollectorsMapBuilder,
    TemplateFlowBuilder,
)
from functools import partial
from xrpl.asyncio.clients import AsyncJsonRpcClient
from fluent.asyncsender import FluentSender
from ekspiper.connect.xrpledger import LedgerCreationDataSource
from ekspiper.connect.queue import QueueSourceSink
from ekspiper.schema.xrp import XRPLTransactionSchema, XRPLObjectSchema
from ekspiper.processor.fetch_transactions import (
    XRPLFetchLedgerDetailsProcessor,
    XRPLExtractTransactionsFromLedgerProcessor,
)
from ekspiper.processor.fetch_book_offers import (
    XRPLFetchBookOffersProcessor, 
    BuildBookOfferRequestsProcessor,
)
from ekspiper.processor.etl import (
    ETLTemplateProcessor,
    GenericValidator,
    XRPLTransactionTransformer,
)
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)


async def stop_template_flows(
    app: web_app.Application,
):
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
    await app["flow_ledger_to_txns_brk"]


async def websocket_supervisor(ledger_creation_source):
    while True:
        try:
            logger.warning("Attempting to connect to server...")
            await ledger_creation_source._start()
        except Exception as e:
            logger.warning("There was an error starting the ledger creation source: " + str(e))

        await asyncio.sleep(10)


async def start_template_flows(
    app: web_app.Application,
    xrpl_endpoint: str = "https://s2.ripple.com:51234/",
    fluent_tag: str = "mainnet.transactions",
    fluent_host: str = "0.0.0.0",
    fluent_port: int = 25225,
    schema: str = "transactions",
):
    async_rpc_client = AsyncJsonRpcClient(xrpl_endpoint)
    fluent_sender = FluentSender(
        fluent_tag,
        host = fluent_host,
        port = fluent_port,
    )

    # build the ledger creation up-to-date data source
    ledger_creation_source = LedgerCreationDataSource(
        wss_url = "wss://s1.ripple.com",
    )

    app["ledger_creation_source_task"] = asyncio.create_task(websocket_supervisor(ledger_creation_source))
    app["ledger_creation_source"] = ledger_creation_source

    ledger_record_source_sink = QueueSourceSink(
        name = "ledger_record_source_sink",
    )
    app["ledger_record_source_sink"] = ledger_record_source_sink

    txn_record_source_sink = QueueSourceSink(
        name = "txn_record_source_sink",
    )
    app["txn_record_source_sink"] = txn_record_source_sink

    app["flow_ledger_details"] = []

    # create 10 tasks of the same to increase throughput
    for i in range(10):
        ledger_details_pc_map_builder = ProcessCollectorsMapBuilder()
        pc_map = ledger_details_pc_map_builder.with_processor(
            XRPLFetchLedgerDetailsProcessor(
                rpc_client = async_rpc_client,
            )
            #).with_stdout_output_collector().build()
        ).add_data_sink_output_collector(
            data_sink = ledger_record_source_sink,
            name = "ledger_record_source_sink",
        ).build()
        flow_ledger_details = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
        app["flow_ledger_details"].append(asyncio.create_task(flow_ledger_details.aexecute(
            message_iterator = ledger_creation_source,
        )))
        # app["flow_ledger_details"] = asyncio.create_task(flow_ledger_details.aexecute(
        #     message_iterator = ledger_creation_source,
        # ))

    
    # Flow: Ledger to Transactions Break Flow
    #
    ledger_to_txns_brk_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = ledger_to_txns_brk_pc_map_builder.with_processor(
        XRPLExtractTransactionsFromLedgerProcessor(
            is_include_ledger_index = True,
        )
    #).with_stdout_output_collector(tag_name = "ledger_brk", is_simplified = True).build()
    ).add_data_sink_output_collector(
        data_sink = txn_record_source_sink,
        name = "txn_record_source_sink",
    ).build()

    flow_ledger_to_txns_brk = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    app["flow_ledger_to_txns_brk"] = asyncio.create_task(flow_ledger_to_txns_brk.aexecute(
        message_iterator = ledger_record_source_sink,
    ))

    schema_to_use = XRPLTransactionSchema.SCHEMA
    if schema == "ledger_object":
        schema_to_use = XRPLObjectSchema.SCHEMA

    logger.warning("Using schema: " + schema)

    # Flow: Transaction Record
    txn_rec_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = txn_rec_pc_map_builder.with_processor(
        ETLTemplateProcessor(
            validator = GenericValidator(schema_to_use),
            transformer = XRPLTransactionTransformer(schema_to_use),
        )
    ).with_stdout_output_collector(
        tag_name = "transactions",
        is_simplified = True
    ).add_fluent_output_collector(
       tag_name = "",
       fluent_sender = fluent_sender,
    ).build()
    flow_txn_record = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    logger.warning("done building, running?")
    app["flow_txn_record"] = asyncio.create_task(flow_txn_record.aexecute(
        message_iterator = txn_record_source_sink,
    ))


def parse_arguments() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument(
        "-ft",
        "--fluent_tag",
        help = "specify the name to tag the FluentD/Bit entries",
        type = str,
        default = None, # use prod for forwarding to GCP
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
        default = "transactions",
    )
    arg_parser.add_argument(
        "-d",
        "--dataset",
        help = "specify the dataset",
        type = str,
        default = "mainnet",
    )
    arg_parser.add_argument(
        "-t",
        "--table",
        help = "specify the table",
        type = str,
        default = "transactions",
    )

    return arg_parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    app = web.Application()
    app.add_routes([
        web.get('/', handle),
        web.get('/{name}', handle),
    ])

    app.on_startup.append(partial(start_template_flows, fluent_tag=args.fluent_tag))
    app.on_cleanup.append(stop_template_flows)
    web.run_app(app)
