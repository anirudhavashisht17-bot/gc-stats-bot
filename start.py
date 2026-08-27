import os
import sys
import asyncio
import subprocess
from aiohttp import web

PORT = int(os.environ.get("PORT", 8080))

async def ping(request):
    return web.Response(text="Bot is running live!")

async def start_web():
    app = web.Application()
    app.router.add_get("/", ping)
    app.router.add_get("/health", ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Server bound on port {PORT}")

def run_original():
    return subprocess.Popen([sys.executable, "gc_stats_bot.py"])

async def main():
    await start_web()
    bot_proc = run_original()
    
    while True:
        if bot_proc.poll() is not None:
            print("Restarting bot...")
            bot_proc = run_original()
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
