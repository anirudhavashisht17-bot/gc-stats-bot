
import os, asyncio, aiohttp, re, yt_dlp

async def safe_download_media(media_url, dest_path):
    if os.path.exists(dest_path):
        try: os.remove(dest_path)
        except: pass
        
    clean = media_url.split("?")[0].strip()
    
    # 1. Instagram 429 Bypass via DDInstagram Proxy Stream
    if "instagram.com" in clean:
        dd_url = clean.replace("instagram.com", "ddinstagram.com")
        headers = {"User-Agent": "TelegramBot (like TwitterBot)"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(dd_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        m = re.search(r'<meta property="og:video" content="([^"]+)"', html)
                        if m:
                            v_url = m.group(1).replace("&amp;", "&")
                            async with session.get(v_url, timeout=aiohttp.ClientTimeout(total=30)) as v_resp:
                                if v_resp.status == 200:
                                    with open(dest_path, "wb") as f_out:
                                        while True:
                                            chunk = await v_resp.content.read(1024 * 1024)
                                            if not chunk: break
                                            f_out.write(chunk)
                                    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
                                        return dest_path
        except Exception as e:
            print(f"DDInstagram stream error: {e}")

    # 2. YT-DLP Mobile Fallback
    try:
        ydl_opts = {
            'outtmpl': dest_path,
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36'
            }
        }
        if "youtu" in clean:
            ydl_opts['extractor_args'] = {'youtube': {'player_client': ['android']}}
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([clean]))
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
            return dest_path
    except Exception as e:
        print(f"Fallback ytdlp error: {e}")
        
    return None


import os, asyncio, aiohttp, urllib.parse, re, yt_dlp

async def fetch_cloud_video(url, out_path):
    if os.path.exists(out_path):
        try:
            os.remove(out_path)
        except Exception:
            pass
            
    clean_url = url.split("?")[0].strip()

    if "instagram.com" in clean_url:
        dd_url = clean_url.replace("instagram.com", "ddinstagram.com")
        headers = {"User-Agent": "TelegramBot (like TwitterBot)"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(dd_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        html = await r.text()
                        m = re.search(r'<meta property="og:video" content="([^"]+)"', html)
                        if m:
                            v_url = m.group(1).replace("&amp;", "&")
                            async with session.get(v_url, timeout=aiohttp.ClientTimeout(total=25)) as vr:
                                if vr.status == 200:
                                    with open(out_path, "wb") as f_out:
                                        f_out.write(await vr.read())
                                    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                                        return out_path
        except Exception:
            pass

    try:
        ydl_opts = {
            "outtmpl": out_path,
            "format": "best[ext=mp4]/best",
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 15,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
            }
        }
        if "youtu" in clean_url:
            ydl_opts["extractor_args"] = {"youtube": {"player_client": ["android"]}}
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([clean_url]))
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            return out_path
    except Exception:
        pass
    return None

import asyncio
import time
import json
import os
import re
import random
import yt_dlp
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.tl.types import ChannelParticipantsAdmins, ChatBannedRights
from telethon.errors import ChatWriteForbiddenError, UserAdminInvalidError

# ==================== CONFIGURATION ====================
API_ID = 33291160
API_HASH = "a19e7fa3783e6e282b70e7fa2969302c"
BOT_TOKEN = "8760068272:AAHbBeLPOvhOEKv6BQ4J0i_dX6M7BvmuU-Y"
ADMIN_ID = 8225211569  # Bot Owner ID

bot = TelegramClient("gc_stats_bot_session", API_ID, API_HASH)
INTRO_VIDEO_PATH = "intro_video.mp4"

# In-Memory Storage
chat_logs = defaultdict(lambda: {"title": "Unknown Group", "messages": []})
user_xp = defaultdict(lambda: defaultdict(lambda: {
    "name": "Member",
    "xp": 0,
    "level": 1,
    "streak": 1,
    "last_date": ""
}))
spam_tracker = defaultdict(list)
banned_words = defaultdict(set)
custom_welcomes = {}  # chat_id -> custom welcome string

def get_rank_title(level):
    if level < 3:
        return "🌱 Rookie"
    elif level < 6:
        return "💬 Chatterbox"
    elif level < 10:
        return "🔥 Elite Talker"
    elif level < 15:
        return "⚡ Chat Master"
    elif level < 25:
        return "👑 GC Legend"
    else:
        return "🌟 Mythic Immortal"

async def is_admin(chat_id, user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        admins = await bot.get_participants(chat_id, filter=ChannelParticipantsAdmins)
        return any(a.id == user_id for a in admins)
    except Exception:
        return False

async def safe_reply(event, text, buttons=None):
    try:
        return await event.reply(text, buttons=buttons)
    except ChatWriteForbiddenError:
        print(f"⚠️ Missing write permission in chat {event.chat_id}")
    except Exception as e:
        print(f"⚠️ Reply Error: {e}")

# ==================== MEDIA DOWNLOADER HELPER ====================
def download_media_sync(url, output_template):
    ydl_opts = {
        'outtmpl': output_template,
        'format': 'best[ext=mp4]/best',
        'max_filesize': 50 * 1024 * 1024,
        'quiet': False,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# ==================== MODERATION: BAN / MUTE / KICK ====================
@bot.on(events.NewMessage(pattern=r"^/ban(?:\s+(.*))?$"))
async def ban_handler(event):
    if not event.is_group:
        return await safe_reply(event, "⚠️ Yeh command sirf group mein kaam karegi!")
    if not await is_admin(event.chat_id, event.sender_id):
        return await safe_reply(event, "❌ Sirf Group Admins ban kar sakte hain.")

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        return await safe_reply(event, "⚠️ Kisi user ke message ko reply karke `/ban` likhein.")

    target_user = await reply_msg.get_sender()
    if not target_user:
        return await safe_reply(event, "❌ Target user nahi mila.")
    if await is_admin(event.chat_id, target_user.id):
        return await safe_reply(event, "❌ Aap kisi Admin ko ban nahi kar sakte!")

    try:
        await bot.edit_permissions(event.chat_id, target_user.id, view_messages=False)
        await safe_reply(event, f"🚫 **User Banned!**\n👤 **User:** {target_user.first_name}\n🆔 **ID:** `{target_user.id}`")
    except Exception as e:
        await safe_reply(event, f"❌ Ban failed: `{e}` (Ensure bot has admin rights)")

@bot.on(events.NewMessage(pattern=r"^/unban(?:\s+(.*))?$"))
async def unban_handler(event):
    if not event.is_group:
        return await safe_reply(event, "⚠️ Yeh command sirf group mein kaam karegi!")
    if not await is_admin(event.chat_id, event.sender_id):
        return await safe_reply(event, "❌ Sirf Group Admins unban kar sakte hain.")

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        return await safe_reply(event, "⚠️ Kisi user ke message ko reply karke `/unban` likhein.")

    target_user = await reply_msg.get_sender()
    try:
        await bot.edit_permissions(event.chat_id, target_user.id, view_messages=True, send_messages=True)
        await safe_reply(event, f"✅ **User Unbanned!**\n👤 **User:** {target_user.first_name}")
    except Exception as e:
        await safe_reply(event, f"❌ Unban failed: `{e}`")

@bot.on(events.NewMessage(pattern=r"^/mute(?:\s+(.*))?$"))
async def mute_handler(event):
    if not event.is_group:
        return await safe_reply(event, "⚠️ Yeh command sirf group mein kaam karegi!")
    if not await is_admin(event.chat_id, event.sender_id):
        return await safe_reply(event, "❌ Sirf Group Admins mute kar sakte hain.")

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        return await safe_reply(event, "⚠️ Kisi user ke message ko reply karke `/mute` likhein.")

    target_user = await reply_msg.get_sender()
    if not target_user:
        return await safe_reply(event, "❌ Target user nahi mila.")
    if await is_admin(event.chat_id, target_user.id):
        return await safe_reply(event, "❌ Aap kisi Admin ko mute nahi kar sakte!")

    try:
        await bot.edit_permissions(event.chat_id, target_user.id, send_messages=False)
        await safe_reply(event, f"🔇 **User Muted!**\n👤 **User:** {target_user.first_name}\n*Ab ye group mein bol nahi payega.*")
    except Exception as e:
        await safe_reply(event, f"❌ Mute failed: `{e}`")

@bot.on(events.NewMessage(pattern=r"^/unmute(?:\s+(.*))?$"))
async def unmute_handler(event):
    if not event.is_group:
        return await safe_reply(event, "⚠️ Yeh command sirf group mein kaam karegi!")
    if not await is_admin(event.chat_id, event.sender_id):
        return await safe_reply(event, "❌ Sirf Group Admins unmute kar sakte hain.")

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        return await safe_reply(event, "⚠️ Kisi user ke message ko reply karke `/unmute` likhein.")

    target_user = await reply_msg.get_sender()
    try:
        await bot.edit_permissions(event.chat_id, target_user.id, send_messages=True)
        await safe_reply(event, f"🔊 **User Unmuted!**\n👤 **User:** {target_user.first_name}")
    except Exception as e:
        await safe_reply(event, f"❌ Unmute failed: `{e}`")

@bot.on(events.NewMessage(pattern=r"^/kick(?:\s+(.*))?$"))
async def kick_handler(event):
    if not event.is_group:
        return await safe_reply(event, "⚠️ Yeh command sirf group mein kaam karegi!")
    if not await is_admin(event.chat_id, event.sender_id):
        return await safe_reply(event, "❌ Sirf Group Admins kick kar sakte hain.")

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        return await safe_reply(event, "⚠️ Kisi user ke message ko reply karke `/kick` likhein.")

    target_user = await reply_msg.get_sender()
    if not target_user:
        return await safe_reply(event, "❌ Target user nahi mila.")
    if await is_admin(event.chat_id, target_user.id):
        return await safe_reply(event, "❌ Aap kisi Admin ko kick nahi kar sakte!")

    try:
        await bot.kick_participant(event.chat_id, target_user.id)
        await safe_reply(event, f"👢 **User Kicked!**\n👤 **User:** {target_user.first_name}")
    except Exception as e:
        await safe_reply(event, f"❌ Kick failed: `{e}`")

# ==================== CUSTOM WELCOME SETTINGS ====================
@bot.on(events.NewMessage(pattern=r"^/setwelcome(?:\s+(.*))?$"))
async def set_welcome_handler(event):
    if not event.is_group:
        return await safe_reply(event, "⚠️ Yeh command sirf group mein kaam karegi!")
    if not await is_admin(event.chat_id, event.sender_id):
        return await safe_reply(event, "❌ Sirf Group Admins custom welcome set kar sakte hain.")

    welcome_text = event.pattern_match.group(1)
    if not welcome_text:
        return await safe_reply(
            event,
            "⚠️ **Format:** `/setwelcome <message>`\n\n"
            "Tags you can use:\n"
            "• `{name}` ➜ Member ka naam\n"
            "• `{title}` ➜ Group ka naam\n\n"
            "**Example:**\n`/setwelcome Hey {name}, welcome to {title}! Enjoy your stay 🌸`"
        )

    custom_welcomes[event.chat_id] = welcome_text
    await safe_reply(event, f"✅ **Custom Welcome Message Saved!**\n\n**Preview:**\n{welcome_text.replace('{name}', event.sender.first_name or 'Member').replace('{title}', event.chat.title or 'Group')}")

@bot.on(events.NewMessage(pattern=r"^/resetwelcome$"))
async def reset_welcome_handler(event):
    if not event.is_group:
        return await safe_reply(event, "⚠️ Yeh command sirf group mein kaam karegi!")
    if not await is_admin(event.chat_id, event.sender_id):
        return await safe_reply(event, "❌ Sirf Group Admins welcome reset kar sakte hain.")

    if event.chat_id in custom_welcomes:
        del custom_welcomes[event.chat_id]
        await safe_reply(event, "🔄 **Welcome message reset to default card!**")
    else:
        await safe_reply(event, "ℹ️ Default welcome message already active hai.")

# ==================== WELCOME & GOODBYE HANDLER ====================
@bot.on(events.ChatAction)
async def welcome_goodbye_handler(event):
    chat_title = event.chat.title if hasattr(event.chat, 'title') else "this group"

    if event.user_joined or event.user_added:
        user = await event.get_user()
        user_name = user.first_name if user else "Friend"

        # Check custom welcome message
        if event.chat_id in custom_welcomes:
            formatted_text = custom_welcomes[event.chat_id].replace("{name}", user_name).replace("{title}", chat_title)
            await safe_reply(event, formatted_text)
        else:
            default_welcome = (
                f"╭────────────────────────╮\n"
                f"  🎉 **NEW MEMBER JOINED**\n"
                f"╰────────────────────────╯\n"
                f"```text\n"
                f"Welcome, {user_name}!\n"
                f"Group: {chat_title}\n"
                f"Tip  : Chat regularly to earn XP & Rank!\n"
                f"```"
            )
            await safe_reply(event, default_welcome)

    elif event.user_left or event.user_kicked:
        user = await event.get_user()
        user_name = user.first_name if user else "Member"
        await safe_reply(event, f"👋 **{user_name}** left the chat. Hope to see you back soon!")

# ==================== WORD BAN & UNBAN ====================
@bot.on(events.NewMessage(pattern=r"^/block(?:\s+(.*))?$"))
async def block_word_handler(event):
    if not event.is_group:
        return await safe_reply(event, "⚠️ Yeh command sirf group mein chalegi!")
    if not await is_admin(event.chat_id, event.sender_id):
        return await safe_reply(event, "❌ Sirf Group Admins words ban kar sakte hain.")

    word = event.pattern_match.group(1)
    if not word:
        return await safe_reply(event, "⚠️ Format: `/block <word>`\nExample: `/block ramesh`")

    word_clean = word.strip().lower()
    banned_words[event.chat_id].add(word_clean)
    await safe_reply(event, f"🚫 **Word Blocked!**\nWord: `{word_clean}`")

@bot.on(events.NewMessage(pattern=r"^/unblock(?:\s+(.*))?$"))
async def unblock_word_handler(event):
    if not event.is_group:
        return await safe_reply(event, "⚠️ Yeh command sirf group mein chalegi!")
    if not await is_admin(event.chat_id, event.sender_id):
        return await safe_reply(event, "❌ Sirf Group Admins words unblock kar sakte hain.")

    word = event.pattern_match.group(1)
    if not word:
        return await safe_reply(event, "⚠️ Format: `/unblock <word>`")

    word_clean = word.strip().lower()
    if word_clean in banned_words[event.chat_id]:
        banned_words[event.chat_id].remove(word_clean)
        await safe_reply(event, f"✅ **Word Unblocked!**\n`{word_clean}` ko ban list se hata diya gaya hai.")
    else:
        await safe_reply(event, f"⚠️ `{word_clean}` ban list mein nahi hai.")

@bot.on(events.NewMessage(pattern=r"^/blockedwords$"))
async def list_blocked_words(event):
    if not event.is_group:
        return
    words = banned_words[event.chat_id]
    word_list = "\n".join([f"• `{w}`" for w in words]) if words else "None"
    await safe_reply(event, f"🚫 **Blocked Words:**\n{word_list}")

# ==================== PING & ID ====================
@bot.on(events.NewMessage(pattern=r"^/ping$"))
async def ping_handler(event):
    start = time.time()
    msg = await event.reply("🏓 **Pinging...**")
    end = time.time()
    latency = (end - start) * 1000
    await msg.edit(f"🏓 **Pong!**\n⚡ **Latency:** `{latency:.2f} ms`")

@bot.on(events.NewMessage(pattern=r"^/id$"))
async def id_handler(event):
    chat_id = event.chat_id
    user_id = event.sender_id
    reply_msg = await event.get_reply_message()
    text = f"🆔 **Identity Panel**\n━━━━━━━━━━━━━━━\n🏢 **Chat ID:** `{chat_id}`\n👤 **Your ID:** `{user_id}`\n"
    if reply_msg:
        text += f"↩️ **Replied User ID:** `{reply_msg.sender_id}`\n"
    await safe_reply(event, text)

# ==================== PERMANENT INTRO VIDEO SAVER ====================
@bot.on(events.NewMessage(incoming=True, func=lambda e: e.is_private and e.video))
async def catch_video(event):
    if event.sender_id == ADMIN_ID:
        status_msg = await event.reply("⏳ **Saving intro video permanently...**")
        try:
            await bot.download_media(event.message, file=INTRO_VIDEO_PATH)
            await status_msg.edit("✅ **Intro Video Saved Permanently!**")
        except Exception as e:
            await status_msg.edit(f"❌ Error saving video: `{e}`")

# ==================== DM START INTRO ====================
@bot.on(events.NewMessage(pattern=r"^/start$"))
async def start_handler(event):
    if event.is_private:
        user = await event.get_sender()
        name = (user.first_name or "USER").upper()
        me = await bot.get_me()

        intro_text = (
            f"╭────────────────────────╮\n"
            f"  🔮 **GROUP PULSE AI ENGINE**\n"
            f"╰────────────────────────╯\n\n"
            f"```yaml\n"
            f"USER    : {name}\n"
            f"SYSTEM  : ONLINE (v2.0)\n"
            f"STATUS  : 24/7 ACTIVE ENGINE\n"
            f"```\n"
            f"```fix\n"
            f"🔥 ACTIVITY, MODERATION & DOWNLOADER ENGINE\n"
            f"```\n\n"
            f"**╭─── 🐱 CORE FEATURES ───╮**\n"
            f"```text\n"
            f"✦ 📊 Real-Time Top 10 Leaderboards\n"
            f"✦ 🏆 XP & Level-Up Progression System\n"
            f"✦ 🛡️ Moderation (/ban, /mute, /kick)\n"
            f"✦ 💌 Custom Welcome Messages (/setwelcome)\n"
            f"✦ 📥 Auto IG Reels & YT Video Downloader\n"
            f"✦ 🚫 Custom Word Blacklist & Auto-Delete\n"
            f"✦ 👑 Global Admin Broadcast Panel\n"
            f"```\n"
            f"**🌸 Tap the buttons below to explore!**"
        )

        buttons = [
            [Button.url("➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ɢʀᴏᴜᴘ 👥", f"https://t.me/{me.username}?startgroup=true")],
            [
                Button.url("👑 ᴏᴡɴᴇʀ", "https://t.me/lll_VIP_VEROX_lll"),
                Button.url("✨ ᴜᴘᴅᴀᴛᴇꜱ", "https://t.me/lll_VEROX_lll")
            ],
            [Button.inline("📖 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅꜱ", b"help_menu")]
        ]

        if os.path.exists(INTRO_VIDEO_PATH) and os.path.getsize(INTRO_VIDEO_PATH) > 0:
            try:
                await bot.send_file(
                    event.chat_id,
                    file=INTRO_VIDEO_PATH,
                    caption=intro_text,
                    buttons=buttons,
                    supports_streaming=True
                )
                return
            except Exception:
                pass

        await safe_reply(event, intro_text, buttons=buttons)
    else:
        await safe_reply(event, "👋 **Group Pulse AI Active!** Use `/stats` or `/level` to view your rankings.")

# ==================== HELP CALLBACK ====================
@bot.on(events.CallbackQuery(data=b"help_menu"))
async def help_callback(event):
    help_text = (
        f"╭────────────────────────╮\n"
        f"  📖 **COMMANDS & MODULES**\n"
        f"╰────────────────────────╯\n\n"
        f"```yaml\n"
        f"[ ACTIVITY & RANKINGS ]\n"
        f"• /stats     : Top 10 Leaderboard (Today/Week/All)\n"
        f"• /level     : Check your XP, Level & Streak\n"
        f"• /mystats   : Your contribution in this group\n"
        f"• /ping      : Check bot latency\n"
        f"• /id        : Get Chat ID & User ID\n"
        f"```\n\n"
        f"```text\n"
        f"[ MODERATION & ADMIN ]\n"
        f"• /ban       : Ban replied user\n"
        f"• /unban     : Unban replied user\n"
        f"• /mute      : Mute replied user\n"
        f"• /unmute    : Unmute replied user\n"
        f"• /kick      : Kick replied user\n"
        f"• /setwelcome: Set custom welcome message\n"
        f"• /resetwelcome: Reset welcome message\n"
        f"• /block <w> : Ban word from chat\n"
        f"• Send IG/YT : Auto video download\n"
        f"```"
    )
    await event.edit(help_text, buttons=[[Button.inline("🔙 ʙᴀᴄᴋ", b"back_start")]])

@bot.on(events.CallbackQuery(data=b"back_start"))
async def back_callback(event):
    await start_handler(event)

# ==================== CORE TRACKER & AUTO DOWNLOADER ====================
@bot.on(events.NewMessage)
async def track_messages(event):
    sender = await event.get_sender()
    if not sender or getattr(sender, 'bot', False):
        return

    raw_text = event.raw_text or ""

        # AUTO MEDIA DOWNLOADER (FIXED)
    media_regex = r"(https?://(?:www\.)?(?:instagram\.com/(?:reel|reels|p|share|tv)/[A-Za-z0-9_.-]+|youtu\.be/[A-Za-z0-9_.-]+|youtube\.com/(?:watch\?v=[A-Za-z0-9_.-]+|shorts/[A-Za-z0-9_.-]+)))"
    match = re.search(media_regex, raw_text)
    if match:
        url = match.group(1)
        rand_id = str(random.randint(10000, 99999))
        target_file = f"media_{rand_id}.mp4"
        try:
            downloaded = await safe_download_media(url, target_file)
            if downloaded and os.path.exists(downloaded):
                await event.reply(file=downloaded)
                if os.path.exists(downloaded):
                    os.remove(downloaded)
                return
        except Exception as e:
            print(f"Auto download error: {e}")
        finally:
            if target_file and os.path.exists(target_file):
                try: os.remove(target_file)
                except: pass
if target_file and os.path.exists(target_file):
                await bot.send_file(event.chat_id, file=target_file, supports_streaming=True)
        except Exception as e:
            print(f"⚠️ Download Error: {e}")
        finally:
            if target_file and os.path.exists(target_file):
                try:
                    os.remove(target_file)
                except Exception:
                    pass

    if not event.is_group:
        return

    chat_id = event.chat_id
    user_id = sender.id
    user_name = sender.first_name or "Member"
    msg_raw = raw_text.lower()

    # 1. WORD BAN CHECK
    if banned_words[chat_id] and not await is_admin(chat_id, user_id):
        for b_word in banned_words[chat_id]:
            if b_word in msg_raw:
                try:
                    await event.delete()
                    warn = await event.respond(f"⚠️ **{user_name}**, banned word use karne par message delete kar diya gaya!")
                    await asyncio.sleep(4)
                    await warn.delete()
                    return
                except Exception:
                    pass

    # 2. ANTI-SPAM CHECK
    now_ts = time.time()
    user_key = (chat_id, user_id)
    spam_tracker[user_key] = [t for t in spam_tracker[user_key] if now_ts - t < 4]
    spam_tracker[user_key].append(now_ts)
    if len(spam_tracker[user_key]) > 5:
        try:
            await event.delete()
            return
        except Exception:
            pass

    if hasattr(event.chat, 'title') and event.chat.title:
        chat_logs[chat_id]["title"] = event.chat.title

    # 3. MESSAGE & XP LOGGING
    chat_logs[chat_id]["messages"].append((now_ts, user_id, user_name))

    today_str = time.strftime("%Y-%m-%d")
    u_data = user_xp[chat_id][user_id]
    u_data["name"] = user_name
    u_data["xp"] += random.randint(5, 10)

    if u_data["last_date"] != today_str:
        yesterday_str = time.strftime("%Y-%m-%d", time.localtime(now_ts - 86400))
        if u_data["last_date"] == yesterday_str:
            u_data["streak"] += 1
        else:
            u_data["streak"] = 1
        u_data["last_date"] = today_str

    required_xp = u_data["level"] * 100
    if u_data["xp"] >= required_xp:
        u_data["level"] += 1
        u_data["xp"] -= required_xp
        rank_title = get_rank_title(u_data["level"])

        lvl_msg = (
            f"╭────────────────────────╮\n"
            f"  🎊 **LEVEL UPGRADED!** 🚀\n"
            f"╰────────────────────────╯\n"
            f"```yaml\n"
            f"USER   : {user_name}\n"
            f"LEVEL  : Level {u_data['level']}\n"
            f"TITLE  : {rank_title}\n"
            f"STREAK : {u_data['streak']} Days 🔥\n"
            f"```"
        )
        asyncio.create_task(safe_reply(event, lvl_msg))

# ==================== LEVEL & STATS ====================
@bot.on(events.NewMessage(pattern=r"^/(level|rank)$"))
async def level_handler(event):
    if not event.is_group:
        return await safe_reply(event, "⚠️ Yeh command sirf groups mein kaam karegi!")
    user = await event.get_sender()
    if not user:
        return

    if user.id not in user_xp[event.chat_id]:
        return await safe_reply(event, "📊 **No XP data yet.** Chat a bit to earn XP!")

    u_data = user_xp[event.chat_id][user.id]
    xp = u_data["xp"]
    level = u_data["level"]
    streak = u_data["streak"]
    required_xp = level * 100
    progress = int((xp / required_xp) * 10)
    bar = "▰" * progress + "▱" * (10 - progress)
    rank_title = get_rank_title(level)

    card = (
        f"╭────────────────────────╮\n"
        f"  👤 **USER PROGRESSION PROFILE**\n"
        f"╰────────────────────────╯\n"
        f"```yaml\n"
        f"NAME   : {user.first_name}\n"
        f"LEVEL  : {level} ({rank_title})\n"
        f"XP     : [{bar}] {xp}/{required_xp}\n"
        f"STREAK : {streak} Days 🔥\n"
        f"```"
    )
    await safe_reply(event, card)

def generate_stats_view(chat_id, timeframe="overall"):
    logs = chat_logs[chat_id]["messages"]
    now = time.time()

    if timeframe == "today":
        cutoff = now - 86400
        header = "TODAY'S ACTIVITY (24H)"
    elif timeframe == "weekly":
        cutoff = now - (86400 * 7)
        header = "WEEKLY ACTIVITY (7 DAYS)"
    else:
        cutoff = 0
        header = "OVERALL ALL-TIME STATS"

    filtered = [m for m in logs if m[0] >= cutoff]
    total_msgs = len(filtered)
    user_counts = defaultdict(lambda: {"count": 0, "name": ""})
    for _, uid, uname in filtered:
        user_counts[uid]["count"] += 1
        user_counts[uid]["name"] = uname

    if total_msgs == 0:
        return f"📊 **{header}**\n━━━━━━━━━━━━━━━━━━━\n⚠️ *Is timeframe mein koi message record nahi hua!*"

    sorted_top = sorted(user_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    ranking_text = ""
    for rank, (uid, data) in enumerate(sorted_top):
        badge = medals[rank] if rank < len(medals) else f"`{rank+1}.`"
        ranking_text += f"{badge} **{data['name']}** ➜ `{data['count']}` msgs\n"

    return (
        f"╭────────────────────────╮\n"
        f"  📊 **{header}** 🚀\n"
        f"╰────────────────────────╯\n"
        f"```yaml\n"
        f"TOTAL MESSAGES : {total_msgs}\n"
        f"ACTIVE MEMBERS : {len(user_counts)}\n"
        f"```\n"
        f"🏆 **TOP 10 ACTIVE CHATTERS:**\n\n{ranking_text}"
        f"━━━━━━━━━━━━━━━━━━━"
    )

@bot.on(events.NewMessage(pattern=r"^/stats$"))
async def group_stats(event):
    if not event.is_group:
        return await safe_reply(event, "⚠️ Yeh command sirf groups mein kaam karegi!")
    msg_text = generate_stats_view(event.chat_id, "overall")
    buttons = [
        [
            Button.inline("📅 Today", b"tf_today"),
            Button.inline("📆 Weekly", b"tf_weekly"),
            Button.inline("🏆 Overall", b"tf_overall")
        ]
    ]
    await safe_reply(event, msg_text, buttons=buttons)

@bot.on(events.CallbackQuery(data=r"^tf_(today|weekly|overall)$"))
async def stats_timeframe_callback(event):
    tf = event.data.decode().split("_")[1]
    msg_text = generate_stats_view(event.chat_id, tf)
    buttons = [
        [
            Button.inline("📅 Today", b"tf_today"),
            Button.inline("📆 Weekly", b"tf_weekly"),
            Button.inline("🏆 Overall", b"tf_overall")
        ]
    ]
    await event.edit(msg_text, buttons=buttons)

@bot.on(events.NewMessage(pattern=r"^/mystats$"))
async def my_stats(event):
    if not event.is_group:
        return await safe_reply(event, "⚠️ Yeh command sirf groups mein kaam karegi!")
    user = await event.get_sender()
    if not user:
        return
    logs = chat_logs[event.chat_id]["messages"]
    total = len(logs)
    user_count = sum(1 for m in logs if m[1] == user.id)
    percentage = (user_count / total * 100) if total > 0 else 0
    await safe_reply(
        event,
        f"╭────────────────────────╮\n"
        f"  👤 **YOUR PERSONAL STATS**\n"
        f"╰────────────────────────╯\n"
        f"```yaml\n"
        f"SENT MESSAGES : {user_count}\n"
        f"CONTRIBUTION  : {percentage:.1f}%\n"
        f"```"
    )

# ==================== ADMIN PANEL & BROADCAST ====================
@bot.on(events.NewMessage(pattern=r"^/admin$"))
async def admin_panel(event):
    if event.sender_id != ADMIN_ID:
        return await safe_reply(event, f"❌ Access Denied.")
    total_groups = len(chat_logs)
    total_all_msgs = sum(len(gc["messages"]) for gc in chat_logs.values())
    group_list = "".join([f"{i}. 🏢 **{gc['title']}** (`{cid}`) ➜ `{len(gc['messages'])}` msgs\n" for i, (cid, gc) in enumerate(chat_logs.items(), 1)])
    await safe_reply(
        event,
        f"🛡️ **Admin Control Panel**\n━━━━━━━━━━━━━━━━━━━\n"
        f"🏢 **Total Groups:** `{total_groups}`\n"
        f"💬 **Total Messages:** `{total_all_msgs}`\n\n"
        f"📋 **Groups:**\n{group_list or 'None'}\n"
    )

@bot.on(events.NewMessage(pattern=r"^/broadcast(?:\s+(.*))?$"))
async def broadcast_handler(event):
    if event.sender_id != ADMIN_ID:
        return await safe_reply(event, "❌ Sirf Admin broadcast kar sakta hai.")
    text_to_send = event.pattern_match.group(1)
    reply_msg = await event.get_reply_message()
    if not text_to_send and not reply_msg:
        return await safe_reply(event, "⚠️ Format: `/broadcast <text>` ya reply karein.")

    status_msg = await event.reply("📢 **Broadcasting...**")
    success, failed = 0, 0
    for chat_id in list(chat_logs.keys()):
        try:
            if reply_msg:
                await bot.forward_messages(chat_id, reply_msg)
            else:
                await bot.send_message(chat_id, text_to_send)
            success += 1
            await asyncio.sleep(0.3)
        except Exception:
            failed += 1
    await status_msg.edit(f"✅ **Broadcast Finished!**\nSent: `{success}` groups | Failed: `{failed}`")

# ==================== MAIN ====================
async def main():
    print("🤖 Bot LIVE with Moderation, Welcome System & Auto Downloader...")
    await bot.start(bot_token=BOT_TOKEN)
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
