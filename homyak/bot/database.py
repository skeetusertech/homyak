import aiosqlite
from .config import DATABASE_PATH

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
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

async def add_user(user_id: int, username: str | None, first_name: str | None, last_name: str | None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, last_name))
        await db.commit()