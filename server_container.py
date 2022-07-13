from aiohttp import web, web_app
from ekspiper.builder.flow import (
    ProcessCollectorsMapBuilder,
    TemplateFlowBuilder,
)
from xrpl.asyncio.clients import AsyncJsonRpcClient
from fluent.asyncsender import FluentSender
from ekspiper.schema.xrp import XRPLTransactionSchema

async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

async def start_background_tasks(
    app: web_app.Application,
):
    ledger_data_source = LedgerSubscriptionDataSource()
    app["ledger_create_listener"] = asyncio.create_task(ledger_data_source.astart())
    
async def cleanup_background_tasks(
    app: web_app.Application,
):
    app["ledger_create_listener"].cancel()
    await app["ledger_create_listener"]


def build_template_flows():
    async_rpc_client = AsyncJsonRpcClient("https://s2.ripple.com:51234/")
    fluent_sender = FluentSender(
        cli_args.environment,
        host = "0.0.0.0", #cli_args.fluent_host,
        port = 22522, #cli_args.fluent_port,
    )


    book_offers_fetch_flow_q = asyncio.Queue()
    txn_record_flow_q = asyncio.Queue()
    book_offers_req_flow_q = asyncio.Queue()


    # Flow: Ledger Details
    #
    ledger_details_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = ledger_details_pc_map_builder.with_processor(
        XRPLFetchLedgerDetailsProcessor(
            rpc_client = async_rpc_client,
        )
    ).add_async_queue_output_collector(
        async_queue = book_offers_fetch_flow_q
    ).add_async_queue_output_collector(
        async_queue = txn_record_flow_q
    ).build()
    flow_ledger_details = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()


    # Flow: Book Offers Fetch Flow
    #
    book_offers_fetch_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = book_offers_fetch_pc_map_builder.with_processor(
        BuildBookOfferRequestsProcessor()
    ).add_async_queue_output_collector(
        async_queue = book_offers_req_flow_q
    ).build()
    flow_booker_offers_fetch = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()


    # Flow: Book Offers Record Flow
    #
    book_offers_rec_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = book_offers_rec_pc_map_builder.with_processor(
        XRPLFetchBookOffersProcessor()
    ).add_fluent_output_collector(
        tag_name = "book_offers",
        fluent_sender = fluent_sender,
    ).build()
    flow_booker_offer_record = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()


    # Flow: Transaction Record Flow
    #
    txn_rec_pc_map_builder = ProcessCollectorsMapBuilder()
    pc_map = txn_rec_pc_map_builder.with_processor(
        ETLTemplateProcessor(
            validator = GenericValidator(XRPLTransactionSchema.SCHEMA),
            transformer = XRPLObjectTransformer(),
        )
    ).add_fluent_output_collector(
        tag_name = "transactions",
        fluent_sender = fluent_sender,
    ).build()
    flow_txn_record = TemplateFlowBuilder().add_process_collectors_map(pc_map).build()


if __name__ == "__main__":
    app = web.Application()
    app.add_routes([
        web.get('/', handle),
        web.get('/{name}', handle),
    ])
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    web.run_app(app)