# This file is a part of TG-FileStreamBot

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from WebStreamer.vars import Var

logger = logging.getLogger("db")

_client: AsyncIOMotorClient = None
_db = None


def get_db():
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(Var.DATABASE_URI)
        _db = _client[Var.DATABASE_NAME]
    return _db


# ── Users ──────────────────────────────────────────────────────────────────────

async def add_user(user_id: int, first_name: str = "", username: str = ""):
    db = get_db()
    await db.users.update_one(
        {"_id": user_id},
        {"$setOnInsert": {
            "_id": user_id,
            "first_name": first_name,
            "username": username,
        }},
        upsert=True,
    )


async def get_all_users():
    db = get_db()
    return await db.users.find({}, {"_id": 1}).to_list(length=None)


async def get_user_count() -> int:
    db = get_db()
    return await db.users.count_documents({})


# ── Stats ──────────────────────────────────────────────────────────────────────

async def inc_upload(file_size: int):
    """Called when a user sends a file to the bot (upload to bot)."""
    db = get_db()
    await db.stats.update_one(
        {"_id": "global"},
        {"$inc": {"upload_bytes": file_size, "file_count": 1}},
        upsert=True,
    )


async def inc_download(bytes_served: int):
    """Called when a web stream request is fully served."""
    db = get_db()
    await db.stats.update_one(
        {"_id": "global"},
        {"$inc": {"download_bytes": bytes_served}},
        upsert=True,
    )


async def get_stats() -> dict:
    db = get_db()
    doc = await db.stats.find_one({"_id": "global"}) or {}
    return {
        "upload_bytes": doc.get("upload_bytes", 0),
        "download_bytes": doc.get("download_bytes", 0),
        "file_count": doc.get("file_count", 0),
    }
