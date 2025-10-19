from typing import Any, Dict, Optional, Tuple
from datetime import datetime
import aiosqlite

from ..config import PROMO_DB_PATH

async def init_db():
    db_path = str(PROMO_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promocodes (
                code TEXT PRIMARY KEY,
                creator_id INTEGER NOT NULL,
                reward_type INTEGER NOT NULL,
                reward_value TEXT,
                duration INTEGER,
                max_uses INTEGER NOT NULL,
                used_count INTEGER DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_uses (
                user_id INTEGER,
                promo_code TEXT,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, promo_code)
            )
        """)
        await db.commit()

async def create_promo(*, code, creator_id, reward_type, reward_value, duration, max_uses) -> bool:
    norm_code = code.strip().upper()
    db_path = str(PROMO_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        try:
            await db.execute("""
                INSERT INTO promocodes (code, creator_id, reward_type, reward_value, duration, max_uses)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(code) DO NOTHING
            """, (norm_code, creator_id, reward_type, reward_value, duration, max_uses))
            await db.commit()
            cur = await db.execute("SELECT changes()")
            (changes,) = await cur.fetchone()
            return changes == 1
        except aiosqlite.IntegrityError:
            return False

async def get_promo(code: str) -> Optional[Dict[str, Any]]:
    db_path = str(PROMO_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM promocodes WHERE code = ?", (code,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    
async def create_or_update_promo(
    db: aiosqlite.Connection,
    code: str,
    reward_type: str,
    reward_value: int,
    max_uses: Optional[int],
    expires_at: Optional[datetime],
) -> None:
    await db.execute(
        """
        INSERT INTO promocodes (code, reward_type, reward_value, max_uses, used, expires_at, created_at, updated_at)
        VALUES (?, ?, ?, ?, 0, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(code) DO UPDATE SET
            reward_type = excluded.reward_type,
            reward_value = excluded.reward_value,
            max_uses    = excluded.max_uses,
            expires_at  = excluded.expires_at,
            updated_at  = CURRENT_TIMESTAMP
        """,
        (code, reward_type, reward_value, max_uses, expires_at),
    )
    await db.commit()


async def redeem_promo(user_id: int, promo_code: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Attempt to redeem a promo code for a user.

    Returns a tuple of (promo, status) where status is one of
    "success", "already_used", "exhausted" or "not_found".
    """

    db_path = str(PROMO_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("BEGIN IMMEDIATE")

        cursor = await db.execute(
            "SELECT * FROM promocodes WHERE code = ?",
            (promo_code,)
        )
        row = await cursor.fetchone()

        if row is None:
            await db.rollback()
            return None, "not_found"

        promo = dict(row)

        if promo["used_count"] >= promo["max_uses"]:
            await db.rollback()
            return promo, "exhausted"

        cursor = await db.execute(
            "SELECT 1 FROM promo_uses WHERE user_id = ? AND promo_code = ?",
            (user_id, promo_code)
        )

        if await cursor.fetchone():
            await db.rollback()
            return promo, "already_used"

        await db.execute(
            "UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?",
            (promo_code,)
        )
        await db.execute(
            "INSERT INTO promo_uses (user_id, promo_code) VALUES (?, ?)",
            (user_id, promo_code)
        )

        promo["used_count"] += 1

        await db.commit()

        return promo, "success"