from aiohttp import web, web_app


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


if __name__ == "__main__":
    app = web.Application()
    app.add_routes([
        web.get('/', handle),
        web.get('/{name}', handle),
    ])
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    web.run_app(app)ㅁ