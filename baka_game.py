import json
import os
import random
import time
from telethon import events

DB_FILE = "baka_economy.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user_data(data, user_id, name):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "name": name,
            "balance": 200,  # $200 Starting bonus
            "is_dead": False,
            "deaths": 0,
            "kills": 0,
            "last_kill_time": 0
        }
    data[uid]["name"] = name
    return data[uid]

def register_baka(bot):

    # Command: /balance ya /bal ya /money
    @bot.on(events.NewMessage(pattern=r"^/(bal|balance|money|wallet)"))
    async def balance_handler(event):
        sender = await event.get_sender()
        if not sender: return
        data = load_data()
        u = get_user_data(data, sender.id, sender.first_name)
        save_data(data)

        status = "💀 Dead" if u["is_dead"] else "💖 Alive"
        msg = (
            f"🏦 **{u['name']} ka Wallet**\n\n"
            f"💰 Balance: **${u['balance']}**\n"
            f"❤️ Status: **{status}**\n"
            f"⚔️ Kills: **{u['kills']}** | ☠️ Deaths: **{u['deaths']}**"
        )
        await event.reply(msg)

    # Command: /kill (Reply to user or tag)
    @bot.on(events.NewMessage(pattern=r"^/kill"))
    async def kill_handler(event):
        if not event.is_group:
            await event.reply("Yeh game sirf groups me chalegi!")
            return

        sender = await event.get_sender()
        if not sender: return
        
        reply_msg = await event.get_reply_message()
        if not reply_msg:
            await event.reply("⚠️ Jise kill karna hai uske message par **reply** karke `/kill` likhein!")
            return

        target = await reply_msg.get_sender()
        if not target or target.bot:
            await event.reply("Bots ko kill nahi kar sakte!")
            return

        if sender.id == target.id:
            await event.reply("Khud ko kill nahi kar sakte! Suicide allowed nahi hai 😂")
            return

        data = load_data()
        killer = get_user_data(data, sender.id, sender.first_name)
        victim = get_user_data(data, target.id, target.first_name)

        # Status check
        if killer["is_dead"]:
            await event.reply(f"💀 **{killer['name']}**, aap mar chuke ho! Pehle `/revive` karo!")
            return

        if victim["is_dead"]:
            await event.reply(f"👻 **{victim['name']}** pehle se hi dead hai! Murde ko kya maroge?")
            return

        # Cooldown check (60 seconds)
        current_time = time.time()
        if current_time - killer["last_kill_time"] < 45:
            remaining = int(45 - (current_time - killer["last_kill_time"]))
            await event.reply(f"⏳ Weapon reload ho raha hai! Ruko **{remaining}s**!")
            return

        # Success rate & Loot
        loot = random.randint(50, 150)
        killer["balance"] += loot
        killer["kills"] += 1
        killer["last_kill_time"] = current_time

        victim["is_dead"] = True
        victim["deaths"] += 1

        save_data(data)

        actions = [
            f"🔫 **{killer['name']}** ne **{victim['name']}** ko headshot mar diya!",
            f"⚔️ **{killer['name']}** ne katana se **{victim['name']}** ke do tukde kar diye!",
            f"💣 **{killer['name']}** ne **{victim['name']}** ke upar RPG blast kar diya!"
        ]
        chosen_action = random.choice(actions)

        await event.reply(
            f"{chosen_action}\n\n"
            f"💵 Loot mili: **+${loot}**\n"
            f"💀 **{victim['name']}** ab mar chuka hai! (Revive fee: $100)"
        )

    # Command: /revive (Revive self or reply to revive friend)
    @bot.on(events.NewMessage(pattern=r"^/revive"))
    async def revive_handler(event):
        if not event.is_group: return
        sender = await event.get_sender()
        if not sender: return

        REVIVE_COST = 100
        data = load_data()
        buyer = get_user_data(data, sender.id, sender.first_name)
        reply_msg = await event.get_reply_message()

        # Case 1: Kisi dost ko revive karna
        if reply_msg:
            target = await reply_msg.get_sender()
            if not target or target.bot:
                await event.reply("Invalid target!")
                return

            friend = get_user_data(data, target.id, target.first_name)
            if not friend["is_dead"]:
                await event.reply(f"💖 **{friend['name']}** toh pehle se zinda hai!")
                return

            if buyer["balance"] < REVIVE_COST:
                await event.reply(f"💸 Dost ko revive karne ke liye **${REVIVE_COST}** chahiye! Aapke paas sirf **${buyer['balance']}** hain.")
                return

            buyer["balance"] -= REVIVE_COST
            friend["is_dead"] = False
            save_data(data)
            await event.reply(f"😇 **{buyer['name']}** ne **${REVIVE_COST}** kharch karke **{friend['name']}** ko jila diya!")
            return

        # Case 2: Khud ko revive karna
        if not buyer["is_dead"]:
            await event.reply(f"💖 **{buyer['name']}**, aap zinda ho! Revive ki zaroorat nahi.")
            return

        if buyer["balance"] < REVIVE_COST:
            # Agar balance kam hai toh emergency free life
            buyer["balance"] = 0
            buyer["is_dead"] = False
            save_data(data)
            await event.reply(f"🏥 Emergency Ward! **{buyer['name']}** ko free ambulance ne bacha liya! (Balance: $0)")
            return

        buyer["balance"] -= REVIVE_COST
        buyer["is_dead"] = False
        save_data(data)
        await event.reply(f"✨ **{buyer['name']}** ne **${REVIVE_COST}** dekar naya jeevan prapt kiya! Ab aap wapas attack kar sakte ho.")
