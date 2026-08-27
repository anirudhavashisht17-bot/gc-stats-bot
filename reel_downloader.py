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

    clean_url = url.split("?")[0].strip()

    # ================= 1. INSTAGRAM (DDInstagram / Fast CDN Engine) =================
    if "instagram.com" in clean_url:
        # Method A: DDInstagram Open API (100% cloud unblocked)
        try:
            dd_url = clean_url.replace("instagram.com", "ddinstagram.com")
            headers = {"User-Agent": "TelegramBot (like TwitterBot)"}
            async with aiohttp.ClientSession() as session:
                async with session.get(dd_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        # Extract og:video directly from server-side render
                        v_match = re.search(r'<meta property="og:video" content="([^"]+)"', html)
                        if v_match:
                            video_direct_url = v_match.group(1).replace("&amp;", "&")
                            async with session.get(video_direct_url, timeout=aiohttp.ClientTimeout(total=30)) as v_resp:
                                if v_resp.status == 200:
                                    with open(output_path, "wb") as f:
                                        while True:
                                            chunk = await v_resp.content.read(1024 * 1024)
                                            if not chunk:
                                                break
                                            f.write(chunk)
                                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                                        return output_path
        except Exception as e:
            print(f"DDInstagram engine error: {e}")

        # Method B: Direct Cobalt V10 Gateway Fallback
        try:
            api_url = "https://api.v10.cobalt.tools/api/json"
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json={"url": clean_url}, headers={"Accept": "application/json"}, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        data = await r.json()
                        if data.get("url"):
                            async with session.get(data["url"], timeout=aiohttp.ClientTimeout(total=25)) as v_resp:
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

    # ================= 2. YOUTUBE & SHORTS (Piped & Invidious Open Streams) =================
    if "youtu" in clean_url:
        video_id = ""
        id_match = re.search(r"(?:v=|\/|be\/|shorts\/)([A-Za-z0-9_-]{11})", clean_url)
        if id_match:
            video_id = id_match.group(1)

        if video_id:
            piped_instances = [
                f"https://pipedapi.kavin.rocks/streams/{video_id}",
                f"https://api.piped.privacydev.net/streams/{video_id}",
                f"https://pipedapi.leptons.xyz/streams/{video_id}"
            ]
            for p_url in piped_instances:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(p_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                video_streams = data.get("videoStreams", [])
                                # Get 720p or 360p pre-merged/direct stream
                                target_stream = None
                                for s in video_streams:
                                    if s.get("format") == "MPEG_4" and not s.get("videoOnly"):
                                        target_stream = s.get("url")
                                        break
                                if not target_stream and video_streams:
                                    target_stream = video_streams[0].get("url")

                                if target_stream:
                                    async with session.get(target_stream, timeout=aiohttp.ClientTimeout(total=30)) as v_resp:
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
