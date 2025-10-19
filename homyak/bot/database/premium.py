import aiosqlite
from datetime import datetime
from ..config import PREMIUM_DB_PATH
from datetime import timedelta, datetime

async def init_db():
    db_path = str(PREMIUM_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS premium (
                user_id INTEGER PRIMARY KEY,
                expires_at TEXT,
                is_lifetime INTEGER NOT NULL DEFAULT 0
            )
        """)
        await db.commit()

async def set_premium(user_id: int, days: int = 0, is_lifetime: bool = False):
    db_path = str(PREMIUM_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        if is_lifetime:
            expires_at = None
        else:
            expires_at = (datetime.now() + timedelta(days=days)).isoformat()
        await db.execute("""
            INSERT INTO premium (user_id, expires_at, is_lifetime)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET 
                expires_at = excluded.expires_at,
                is_lifetime = excluded.is_lifetime
        """, (user_id, expires_at, 1 if is_lifetime else 0))
        await db.commit()

async def get_premium(user_id: int) -> dict | None:
    db_path = str(PREMIUM_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT expires_at, is_lifetime FROM premium WHERE user_id = ?", 
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return {
                "expires_at": row[0],
                "is_lifetime": row[1] == 1
            }
        return None

async def is_premium_active(user_id: int) -> bool:
    premium = await get_premium(user_id)
    if not premium:
        return False
    if premium["is_lifetime"]:
        return True
    if premium["expires_at"]:
        return datetime.fromisoformat(premium["expires_at"]) > datetime.now()
    return False

async def remove_premium(user_id: int):
    db_path = str(PREMIUM_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("DELETE FROM premium WHERE user_id = ?", (user_id,))
        await db.commit()