import os
import sys
import asyncio
import subprocess
from aiohttp import web

PORT = int(os.environ.get("PORT", 8080))

async def ping(request):
    return web.Response(text="GC Stats Bot is running live!")

async def start_web():
    app = web.Application()
    app.router.add_get("/", ping)
    app.router.add_get("/health", ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Web server started on port {PORT}")

def run_bot():
    return subprocess.Popen([sys.executable, "gc_stats_bot.py"])

async def main():
    await start_web()
    bot_process = run_bot()
    print("GC Stats Bot process started.")
    
    # Process ko monitor karte rahenge
    while True:
        if bot_process.poll() is not None:
            print("Bot crashed or stopped, restarting...")
            bot_process = run_bot()
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
