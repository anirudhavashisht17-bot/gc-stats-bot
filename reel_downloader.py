import os
import asyncio
import aiohttp
import urllib.parse
import yt_dlp

async def download_media(url: str, output_path: str = "downloaded_video.mp4") -> str:
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception:
            pass

    clean_url = url.split("?")[0].strip()

    # 1. INSTAGRAM REELS (High Reliability Fast CDN)
    if "instagram.com" in clean_url:
        shortcode_match = clean_url.rstrip("/").split("/")[-1]
        
        # Endpoint A: Direct GraphQL Media API
        graphql_url = f"https://www.instagram.com/graphql/query/?query_hash=b3055c01b4b222b8a47dc12b090e4e64&variables=%7B%22shortcode%22:%22{shortcode_match}%22%7D"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(graphql_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        v_url = data.get("data", {}).get("shortcode_media", {}).get("video_url")
                        if v_url:
                            async with session.get(v_url, timeout=aiohttp.ClientTimeout(total=25)) as v_resp:
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

        # Endpoint B: Multi-Region Proxy API
        backup_apis = [
            f"https://api.siputzx.my.id/api/d/igdl?url={urllib.parse.quote(clean_url)}",
            f"https://api.ryzendesu.vip/api/downloader/igdl?url={urllib.parse.quote(clean_url)}"
        ]
        for api in backup_apis:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(api, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            res = await resp.json()
                            dl = None
                            if isinstance(res.get("data"), list) and res["data"]:
                                dl = res["data"][0].get("url")
                            elif isinstance(res.get("data"), dict):
                                dl = res["data"].get("url") or res["data"].get("video_url")
                            elif res.get("url"):
                                dl = res.get("url")
                                
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

    # 2. YOUTUBE & SHORTS (Native Android Client - Unblocked)
    if "youtu" in clean_url:
        try:
            ydl_opts = {
                'outtmpl': output_path,
                'format': 'best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 15,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android']
                    }
                }
            }
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([clean_url]))
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                return output_path
        except Exception:
            pass

    return None
