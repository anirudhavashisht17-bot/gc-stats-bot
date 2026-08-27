import os
import asyncio
import aiohttp
import urllib.parse

async def download_media(url: str, output_path: str = "downloaded_video.mp4") -> str:
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception:
            pass

    clean_url = url.split("?")[0].strip()

    # Multi-Engine CDN Streamers
    endpoints = [
        f"https://api.vkrdownloader.xyz/server?v=v2&api_key=vkr_99&url={urllib.parse.quote(clean_url)}",
        f"https://api.siputzx.my.id/api/d/igdl?url={urllib.parse.quote(clean_url)}",
        f"https://api.ryzendesu.vip/api/downloader/igdl?url={urllib.parse.quote(clean_url)}"
    ]

    for api in endpoints:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        dl = None
                        if isinstance(data.get("data"), list) and data["data"]:
                            dl = data["data"][0].get("url")
                        elif isinstance(data.get("data"), dict):
                            dl = data["data"].get("url") or data["data"].get("video_url")
                        elif data.get("download_url") or data.get("url"):
                            dl = data.get("download_url") or data.get("url")

                        if dl:
                            async with session.get(dl, timeout=aiohttp.ClientTimeout(total=25)) as v_resp:
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

    return None
