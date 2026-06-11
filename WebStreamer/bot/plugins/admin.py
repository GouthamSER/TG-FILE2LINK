# This file is a part of TG-FileStreamBot

import asyncio
import logging
from pyrogram import filters
from pyrogram.types import Message
from WebStreamer.vars import Var
from WebStreamer.bot import StreamBot

logger = logging.getLogger("admin")

_db_enabled = bool(Var.DATABASE_URI)

if _db_enabled:
    from WebStreamer.db import get_user_count, get_all_users, get_stats


def owner_filter(_, __, m: Message):
    return m.from_user and m.from_user.id == Var.OWNER_ID


def human_bytes(n: int) -> str:
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PiB"


@StreamBot.on_message(filters.command("stats") & filters.private & filters.create(owner_filter))
async def stats_cmd(_, m: Message):
    if not _db_enabled:
        return await m.reply("⚠️ <b>DATABASE_URI not set.</b> Stats unavailable.", quote=True)

    users = await get_user_count()
    stats = await get_stats()

    text = (
        "📊 <b>Bot Statistics</b>\n\n"
        f"👥 <b>Total Users:</b> <code>{users}</code>\n"
        f"📤 <b>Files Uploaded:</b> <code>{stats['file_count']}</code>\n"
        f"📦 <b>Data Uploaded:</b> <code>{human_bytes(stats['upload_bytes'])}</code>\n"
        f"📥 <b>Data Served:</b> <code>{human_bytes(stats['download_bytes'])}</code>"
    )
    await m.reply(text, quote=True)


@StreamBot.on_message(filters.command("broadcast") & filters.private & filters.create(owner_filter))
async def broadcast_cmd(bot, m: Message):
    if not _db_enabled:
        return await m.reply("⚠️ <b>DATABASE_URI not set.</b> Broadcast unavailable.", quote=True)

    msg = m.reply_to_message
    if not msg:
        return await m.reply(
            "Reply to a message to broadcast it.\n"
            "<code>/broadcast</code> → reply to the message you want to send.",
            quote=True,
        )

    users = await get_all_users()
    total = len(users)
    sent = failed = 0

    status = await m.reply(f"📢 Broadcasting to <b>{total}</b> users...", quote=True)

    for doc in users:
        uid = doc["_id"]
        try:
            await msg.copy(uid)
            sent += 1
        except Exception as e:
            logger.warning(f"Broadcast failed for {uid}: {e}")
            failed += 1
        await asyncio.sleep(0.05)  # flood guard

    await status.edit(
        f"✅ <b>Broadcast complete.</b>\n\n"
        f"📨 Sent: <code>{sent}</code>\n"
        f"❌ Failed: <code>{failed}</code>"
    )
