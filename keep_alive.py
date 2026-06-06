import asyncio
import threading
from aiohttp import web


async def health(request):
    return web.Response(text="✅ CinemaCityHub is running!", status=200)


async def start_web_server():
    app = web.Application()
    app.router.add_get("/",       health)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("[KEEP-ALIVE] Web server running on port 8080")


def run_keep_alive():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_web_server())
    loop.run_forever()
