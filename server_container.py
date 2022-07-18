from aiohttp import web, web_app
import asyncio
from ekspiper.builder.flow import (
    ProcessCollectorsMapBuilder,
    TemplateFlowBuilder,
)
from xrpl.asyncio.clients import AsyncJsonRpcClient
from fluent.asyncsender import FluentSender
from ekspiper.connect.xrpledger import LedgerCreationDataSource
from ekspiper.connect.queue import QueueSource
from ekspiper.schema.xrp import XRPLTransactionSchema
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

#async def start_background_tasks(
#    app: web_app.Application,
#):
#    ledger_data_source = LedgerSubscriptionDataSource()
#    app["ledger_create_listener"] = asyncio.create_task(ledger_data_source.astart())
#    
#async def cleanup_background_tasks(
#    app: web_app.Application,
#):
#    app["ledger_create_listener"].cancel()
#    await app["ledger_create_listener"]

async def stop_template_flows(
    app: web_app.Application,
):
    # theoretically, if we stop the sources, flow should
    # drain out and exit gracefully
    app["ledger_creation_source"].stop()
    app["book_offers_fetch_flow_source"].stop()
    app["book_offers_req_flow_source"].stop()
    app["ledger_record_source"].stop()
    app["txn_record_source"].stop()

    # now wait for them to drain
    await app["flow_ledger_details"]
    await app["flow_booker_offers_fetch"]
    for r in app["flow_booker_offer_records"]:
        await r
    await app["flow_txn_record"]
    await app["flow_ledger_to_txns_brk"]

async def start_template_flows(
    app: web_app.Application,
):

    async_rpc_client = AsyncJsonRpcClient("https://s2.ripple.com:51234/")
    fluent_sender = FluentSender(
        "local", #cli_args.environment,
        host = "0.0.0.0", #cli_args.fluent_host,
        port = 22522, #cli_args.fluent_port,
    )

    book_offers_fetch_flow_q = asyncio.Queue()
    ledger_record_flow_q = asyncio.Queue()
    txn_record_flow_q = asyncio.Queue()
    book_offers_req_flow_q = asyncio.Queue()


    # build the ledger creation up-to-date data source
    ledger_creation_source = LedgerCreationDataSource(
        wss_url = "wss://s1.ripple.com",
    )
    ledger_creation_source.start()
    app["ledger_creation_source"] = ledger_creation_source

    # build the queue source
    book_offers_fetch_flow_source = QueueSource(
        name = "book_offers_fetch_flow_source",
        async_queue = book_offers_fetch_flow_q,
    )
    app["book_offers_fetch_flow_source"] = book_offers_fetch_flow_source

    book_offers_req_flow_source = QueueSource(
        name = "book_offers_req_flow_source",
        async_queue = book_offers_req_flow_q,
    )
    app["book_offers_req_flow_source"] = book_offers_req_flow_source

    ledger_record_source = QueueSource(
        name = "ledger_record_source",
        async_queue = ledger_record_flow_q,
    )
    app["ledger_record_source"] = ledger_record_source

    txn_record_source = QueueSource(
        name = "txn_record_source",
        async_queue = txn_record_flow_q,
    )
    app["txn_record_source"] = txn_record_source

    # Flow: Ledger Details
    #
    ledger_details_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = ledger_details_pc_map_builder.with_processor(
        XRPLFetchLedgerDetailsProcessor(
            rpc_client = async_rpc_client,
        )
    #).with_stdout_output_collector().build()
    ).add_async_queue_output_collector(
        async_queue = book_offers_fetch_flow_q,
        name = "book_offers_fetch_flow_q",
    ).add_async_queue_output_collector(
        async_queue = ledger_record_flow_q,
        name = "ledger_record_flow_q",
    ).build()
    flow_ledger_details = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    app["flow_ledger_details"] = asyncio.create_task(flow_ledger_details.aexecute(
        message_iterator = ledger_creation_source,
    ))

    
    # Flow: Book Offers Fetch Flow
    #
    book_offers_fetch_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = book_offers_fetch_pc_map_builder.with_processor(
        BuildBookOfferRequestsProcessor()
    #).with_stdout_output_collector().build()
    ).add_async_queue_output_collector(
        async_queue = book_offers_req_flow_q
    ).build()
    flow_booker_offers_fetch = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    app["flow_booker_offers_fetch"] = asyncio.create_task(flow_booker_offers_fetch.aexecute(
        message_iterator = book_offers_fetch_flow_source,
    ))

    
    # Flow: Book Offers Record Flow
    #
    app["flow_booker_offer_records"] = []

    # create 10 tasks of the same to increase throughput
    for i in range(10):
        book_offers_rec_pc_map_builder = ProcessCollectorsMapBuilder()
        pc_map = book_offers_rec_pc_map_builder.with_processor(
            XRPLFetchBookOffersProcessor(
                rpc_client = async_rpc_client,
            )
        ).with_stdout_output_collector(tag_name = "book_offers", is_simplified = True).build()
        # TODO: Enable when fluent is ready.
        #).add_fluent_output_collector(
        #    tag_name = "book_offers",
        #    fluent_sender = fluent_sender,
        #).build()
        flow_booker_offer_record = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
        app["flow_booker_offer_records"].append(asyncio.create_task(flow_booker_offer_record.aexecute(
            message_iterator = book_offers_req_flow_source,
        )))

    
    # Flow: Ledger to Transactions Break Flow
    #
    ledger_to_txns_brk_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = ledger_to_txns_brk_pc_map_builder.with_processor(
        XRPLExtractTransactionsFromLedgerProcessor()
    #).with_stdout_output_collector(tag_name = "ledger_brk", is_simplified = True).build()
    ).add_async_queue_output_collector(
        async_queue = txn_record_flow_q,
    ).build()
    flow_ledger_to_txns_brk = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    app["flow_ledger_to_txns_brk"] = asyncio.create_task(flow_ledger_to_txns_brk.aexecute(
        message_iterator = ledger_record_source,
    ))

    
    # Flow: Transaction Record
    txn_rec_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = txn_rec_pc_map_builder.with_processor(
        ETLTemplateProcessor(
            validator = GenericValidator(XRPLTransactionSchema.SCHEMA),
            transformer = XRPLTransactionTransformer(),
        )
    ).with_stdout_output_collector(tag_name = "transactions", is_simplified = True).build()
    # TODO: Enable when fluent is ready
    #).add_fluent_output_collector(
    #    tag_name = "transactions",
    #    fluent_sender = fluent_sender,
    #).build()
    flow_txn_record = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()
    app["flow_txn_record"] = asyncio.create_task(flow_txn_record.aexecute(
        message_iterator = txn_record_source,
    ))
    

if __name__ == "__main__":
    app = web.Application()
    app.add_routes([
        web.get('/', handle),
        web.get('/{name}', handle),
    ])
    app.on_startup.append(start_template_flows)
    app.on_cleanup.append(stop_template_flows)
    web.run_app(app)