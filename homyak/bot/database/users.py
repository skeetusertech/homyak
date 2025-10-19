import aiosqlite
from ..config import USERS_DB_PATH
from pathlib import Path

async def init_db():
    db_path = str(USERS_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_user_and_check(user_id: int, username: str | None, first_name: str | None, last_name: str | None) -> bool:
    db_path = str(USERS_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        exists = await cursor.fetchone()
        if exists:
            return False 

        await db.execute(
            "INSERT INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, last_name)
        )
        await db.commit()
        return True