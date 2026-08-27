import os
import sys
import asyncio
from aiohttp import web

PORT = int(os.environ.get("PORT", 8080))

async def ping(request):
    return web.Response(text="GC Stats Bot is Running 24/7!")

async def start_web():
    app = web.Application()
    app.router.add_get("/", ping)
    app.router.add_get("/health", ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"✅ Web server bound to port {PORT}")

async def main():
    await start_web()
    
    # Import and run the actual bot script inside the same async event loop
    print("🚀 Initializing gc_stats_bot...")
    try:
        import gc_stats_bot
        # Agar gc_stats_bot ke andar client object hai
        if hasattr(gc_stats_bot, 'bot') and hasattr(gc_stats_bot.bot, 'run_until_disconnected'):
            await gc_stats_bot.bot.run_until_disconnected()
        elif hasattr(gc_stats_bot, 'client') and hasattr(gc_stats_bot.client, 'run_until_disconnected'):
            await gc_stats_bot.client.run_until_disconnected()
        else:
            # Fallback event loop keep alive
            while True:
                await asyncio.sleep(3600)
    except Exception as e:
        print(f"❌ Error in bot runtime: {e}")
        # Run fallback execution
        os.system(f"{sys.executable} gc_stats_bot.py")

if __name__ == "__main__":
    asyncio.run(main())
