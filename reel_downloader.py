import re
import os
import aiohttp
import asyncio

async def download_media(link: str, output_path: str = "downloaded_video.mp4") -> str:
    # Multiple Fast CDN Extractors (No IP Block / Pre-merged MP4)
    gateways = [
        "https://api.v2.cobalt.tools/api/json",
        "https://cobalt-api.kwiatekm.pl/api/json",
        "https://api.cobalt.lol/api/json",
        "https://dl.stream-api.org/api/json"
    ]
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {
        "url": link,
        "vQuality": "720"
    }

    for gw in gateways:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(gw, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
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

    # Fallback to direct public scrapers
    try:
        insta_api = f"https://api.tiklydown.eu.org/api/download?url={link}"
        async with aiohttp.ClientSession() as session:
            async with session.get(insta_api, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    direct_url = data.get("video_url") or data.get("url") or (data.get("result", [{}])[0].get("url") if isinstance(data.get("result"), list) else None)
                    if direct_url:
                        async with session.get(direct_url, timeout=aiohttp.ClientTimeout(total=20)) as v_resp:
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
        pass

    return None
