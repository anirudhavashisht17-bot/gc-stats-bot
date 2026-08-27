import os
import asyncio
from aiohttp import web

PORT = int(os.environ.get("PORT", 8080))

async def ping(request):
    return web.Response(text="GC Stats Bot is running live!")

async def start_web():
    app = web.Application()
    app.router.add_get("/", ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def main():
    await start_web()
    # gc_stats_bot.py ko import aur execute karega
    import gc_stats_bot

if __name__ == "__main__":
    asyncio.run(main())
