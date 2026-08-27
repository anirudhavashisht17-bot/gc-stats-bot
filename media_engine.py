import os
import re
import asyncio
import aiohttp
import urllib.parse
import yt_dlp

RAPID_KEY = "9cfbb4bd04msh1d488345e667892p1f39f8jsn14613858a6c0"
RAPID_HOST = "instagram-reels-downloader-api.p.rapidapi.com"

async def get_video(url: str, out_name: str) -> str:
    if os.path.exists(out_name):
        try:
            os.remove(out_name)
        except Exception:
            pass

    clean_url = url.split("?")[0].strip()

    # --- 1. INSTAGRAM REELS / POSTS (RapidAPI Dedicated Gateway) ---
    if "instagram.com" in clean_url:
        api_url = f"https://{RAPID_HOST}/download"
        headers = {
            "x-rapidapi-key": RAPID_KEY,
            "x-rapidapi-host": RAPID_HOST,
            "Content-Type": "application/json"
        }
        params = {"url": clean_url}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        dl_url = None
                        
                        # API response parsing (covers all formats)
                        if isinstance(data, list) and len(data) > 0:
                            dl_url = data[0].get("download_link") or data[0].get("url")
                        elif isinstance(data, dict):
                            dl_url = data.get("download_link") or data.get("url") or data.get("video_url")
                            if not dl_url and "data" in data:
                                if isinstance(data["data"], list) and len(data["data"]) > 0:
                                    dl_url = data["data"][0].get("download_link") or data["data"][0].get("url")
                                elif isinstance(data["data"], dict):
                                    dl_url = data["data"].get("download_link") or data["data"].get("url") or data["data"].get("video_url")

                        if dl_url:
                            async with session.get(dl_url, timeout=aiohttp.ClientTimeout(total=30)) as v_resp:
                                if v_resp.status == 200:
                                    with open(out_name, "wb") as f_out:
                                        while True:
                                            chunk = await v_resp.content.read(1024 * 1024)
                                            if not chunk:
                                                break
                                            f_out.write(chunk)
                                    if os.path.exists(out_name) and os.path.getsize(out_name) > 1000:
                                        return out_name
        except Exception as e:
            print(f"RapidAPI Instagram Error: {e}")

    # --- 2. YOUTUBE & SHORTS (Android Mobile Client Bypass) ---
    try:
        ydl_opts = {
            'outtmpl': out_name,
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'
            }
        }
        if "youtu" in clean_url:
            ydl_opts['extractor_args'] = {'youtube': {'player_client': ['android']}}

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([clean_url]))
        if os.path.exists(out_name) and os.path.getsize(out_name) > 1000:
            return out_name
    except Exception as e:
        print(f"yt-dlp Fallback Error: {e}")

    return None
