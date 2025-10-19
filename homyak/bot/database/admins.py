
import aiosqlite
from ..config import ADMINS_DB_PATH

async def init_db():
    db_path = str(ADMINS_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                is_owner INTEGER NOT NULL DEFAULT 0  -- 1 = главный админ
            )
        """)
        await db.execute(
            "INSERT OR IGNORE INTO admins (user_id, is_owner) VALUES (?, 1)",
            (7869783590,)
        )
        await db.commit()

async def is_admin(user_id: int) -> bool:
    db_path = str(ADMINS_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        return await cursor.fetchone() is not None

async def is_owner(user_id: int) -> bool:
    db_path = str(ADMINS_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT is_owner FROM admins WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row is not None and row[0] == 1

async def add_admin(user_id: int, by_owner: bool = False):
    db_path = str(ADMINS_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR IGNORE INTO admins (user_id, is_owner) VALUES (?, 0)",
            (user_id,)
        )
        await db.commit()

async def remove_admin(user_id: int, remover_id: int):
    if user_id == 7869783590:
        return False
    if not await is_admin(remover_id):
        return False
    db_path = str(ADMINS_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await db.commit()
        return True