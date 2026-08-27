import re
import os
import aiohttp
import asyncio

async def download_media(link: str, output_path: str = "downloaded_video.mp4") -> str:
    # Source 1: Universal Video Parsing Engine
    apis = [
        f"https://api.v2.cobalt.tools/api/json",
        f"https://api.cobalt.lol/api/json"
    ]
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    payload = {"url": link, "vQuality": "720"}

    for api in apis:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        res = await r.json()
                        v_url = res.get("url")
                        if v_url:
                            async with session.get(v_url, timeout=aiohttp.ClientTimeout(total=30)) as vid:
                                if vid.status == 200:
                                    with open(output_path, "wb") as f:
                                        while True:
                                            chunk = await vid.content.read(1024 * 1024)
                                            if not chunk:
                                                break
                                            f.write(chunk)
                                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                                        return output_path
        except Exception:
            continue

    # Source 2: Direct Scraper API for Instagram / YouTube
    try:
        fb_api = f"https://api.tiklydown.eu.org/api/download?url={link}"
        async with aiohttp.ClientSession() as session:
            async with session.get(fb_api, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    data = await r.json()
                    direct = data.get("video_url") or data.get("url")
                    if direct:
                        async with session.get(direct, timeout=aiohttp.ClientTimeout(total=30)) as vid:
                            if vid.status == 200:
                                with open(output_path, "wb") as f:
                                    while True:
                                        chunk = await vid.content.read(1024 * 1024)
                                        if not chunk:
                                            break
                                        f.write(chunk)
                                if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                                    return output_path
    except Exception:
        pass

    return None
