import os
import asyncio
import aiohttp
import urllib.parse
import re

async def download_media(url: str, output_path: str = "downloaded_video.mp4") -> str:
    # Clean previous garbage
    if os.path.exists(output_path):
        os.remove(output_path)

    # Strategy 1: Fast Direct Instagram CDN Scraper (No Token Required)
    if "instagram.com" in url:
        try:
            encoded_url = urllib.parse.quote(url, safe='')
            api_endpoint = f"https://api.siputzx.my.id/api/d/igdl?url={encoded_url}"
            async with aiohttp.ClientSession() as session:
                async with session.get(api_endpoint, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        video_urls = []
                        if isinstance(data.get("data"), list):
                            for item in data["data"]:
                                if item.get("url"):
                                    video_urls.append(item["url"])
                        elif isinstance(data.get("data"), dict) and data["data"].get("url"):
                            video_urls.append(data["data"]["url"])

                        if video_urls:
                            target_v = video_urls[0]
                            async with session.get(target_v, timeout=aiohttp.ClientTimeout(total=30)) as v_resp:
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
            print(f"IG Direct API Failed: {e}")

    # Strategy 2: Fast YouTube Short / Video Resolver
    if "youtu" in url:
        try:
            clean_yt = url.split("?")[0]
            encoded_url = urllib.parse.quote(clean_yt, safe='')
            api_endpoint = f"https://api.siputzx.my.id/api/d/ytmp4?url={encoded_url}"
            async with aiohttp.ClientSession() as session:
                async with session.get(api_endpoint, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        dl_link = data.get("data", {}).get("dl") or data.get("dl")
                        if dl_link:
                            async with session.get(dl_link, timeout=aiohttp.ClientTimeout(total=35)) as v_resp:
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
            print(f"YT Direct API Failed: {e}")

    # Strategy 3: Multi-Platform Universal Stream Fallback
    try:
        encoded_url = urllib.parse.quote(url, safe='')
        universal_api = f"https://api.agatz.xyz/api/instagram?url={encoded_url}" if "instagram.com" in url else f"https://api.agatz.xyz/api/ytmp4?url={encoded_url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(universal_api, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    dl = data.get("data", {}).get("url") or data.get("data", [{}])[0].get("url")
                    if dl:
                        async with session.get(dl, timeout=aiohttp.ClientTimeout(total=30)) as v_resp:
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
        print(f"Universal Scraper Failed: {e}")

    # Strategy 4: Local yt-dlp (Low Quality Single Stream to avoid ffmpeg merge requirement)
    try:
        import yt_dlp
        ydl_opts = {
            'outtmpl': output_path,
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
            }
        }
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
            return output_path
    except Exception as e:
        print(f"Local yt-dlp Fallback Failed: {e}")

    return None
