import os
import re
import asyncio
import aiohttp
import urllib.parse

async def download_media(url: str, output_path: str = "downloaded_video.mp4") -> str:
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception:
            pass

    # Clean URL
    url = url.split("?")[0].strip()

    # --- 1. INSTAGRAM GRAPH DIRECT SCRAPER ---
    if "instagram.com" in url:
        try:
            ig_api = f"https://api.vkrdownloader.xyz/server/instagram?url={urllib.parse.quote(url)}"
            async with aiohttp.ClientSession() as session:
                async with session.get(ig_api, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        v_link = data.get("data", {}).get("video_url") or data.get("video_url")
                        if v_link:
                            async with session.get(v_link, timeout=aiohttp.ClientTimeout(total=30)) as v_resp:
                                if v_resp.status == 200:
                                    with open(output_path, "wb") as f:
                                        while True:
                                            chunk = await v_resp.content.read(1024 * 1024)
                                            if not chunk:
                                                break
                                            f.write(chunk)
                                    if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
                                        return output_path
        except Exception as e:
            print(f"Instagram Direct Engine Error: {e}")

    # --- 2. YOUTUBE / UNIVERSAL FAST STREAM API ---
    universal_endpoints = [
        f"https://api.ryzendesu.vip/api/downloader/ytmp4?url={urllib.parse.quote(url)}",
        f"https://api.ryzendesu.vip/api/downloader/igdl?url={urllib.parse.quote(url)}",
        f"https://api.dorratz.com/v2/ig-dl?url={urllib.parse.quote(url)}"
    ]

    for ep in universal_endpoints:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(ep, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        dl_url = (
                            data.get("url") or 
                            data.get("download", {}).get("url") or 
                            (data.get("data", [{}])[0].get("url") if isinstance(data.get("data"), list) and data.get("data") else None)
                        )
                        if dl_url:
                            async with session.get(dl_url, timeout=aiohttp.ClientTimeout(total=30)) as v_resp:
                                if v_resp.status == 200:
                                    with open(output_path, "wb") as f:
                                        while True:
                                            chunk = await v_resp.content.read(1024 * 1024)
                                            if not chunk:
                                                break
                                            f.write(chunk)
                                    if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
                                        return output_path
        except Exception:
            continue

    # --- 3. HARDWARE YT-DLP FALLBACK (Single Format, No Merging Required) ---
    try:
        import yt_dlp
        ydl_opts = {
            'outtmpl': output_path,
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'socket_timeout': 15,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            }
        }
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
            return output_path
    except Exception as e:
        print(f"yt-dlp Execution Error: {e}")

    return None
