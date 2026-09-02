import asyncio
from telethon import events

def register_utag(bot):
    @bot.on(events.NewMessage(pattern=r"^/utag(?:\s+(.*))?"))
    async def mention_all_handler(event):
        if not event.is_group:
            await event.reply("Yeh command sirf groups me kaam karegi!")
            return

        chat = await event.get_chat()
        custom_msg = event.pattern_match.group(1)
        if not custom_msg:
            reply_msg = await event.get_reply_message()
            if reply_msg and reply_msg.text:
                custom_msg = reply_msg.text
            else:
                custom_msg = "Hello everyone!"

        status_msg = await event.reply("Members fetch ho rahe hain...")

        mentions = []
        async for user in event.client.iter_participants(chat):
            if user.bot or user.deleted:
                continue
            first_name = user.first_name or "Member"
            mentions.append(f"[{first_name}](tg://user?id={user.id})")

        if not mentions:
            await status_msg.edit("Koi tag karne layak member nahi mila.")
            return

        await status_msg.delete()

        batch_size = 5
        for i in range(0, len(mentions), batch_size):
            batch = mentions[i:i + batch_size]
            tags = " ".join(batch)
            msg_to_send = f"{custom_msg}\n\n{tags}"
            await event.client.send_message(chat, msg_to_send)
            await asyncio.sleep(1.5)
