import re
import os
import aiohttp
import asyncio

async def download_media(link: str, output_path: str = "downloaded_video.mp4") -> str:
    # Cobalt public API endpoints
    apis = [
        "https://api.cobalt.tools/api/json",
        "https://cobalt.api.screc.me/api/json"
    ]
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    payload = {"url": link, "vQuality": "720"}

    for api_url in apis:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        media_url = data.get("url")
                        if media_url:
                            async with session.get(media_url, timeout=aiohttp.ClientTimeout(total=25)) as v_resp:
                                if v_resp.status == 200:
                                    with open(output_path, "wb") as f:
                                        while True:
                                            chunk = await v_resp.content.read(1024 * 1024)
                                            if not chunk:
                                                break
                                            f.write(chunk)
                                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                                        return output_path
        except Exception:
            continue

    # Fallback to yt-dlp with optimized headers
    try:
        import yt_dlp
        ydl_opts = {
            'outtmpl': output_path,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([link]))
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return output_path
    except Exception:
        pass

    return None
