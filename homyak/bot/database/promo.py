import aiosqlite
from ..config import PROMO_DB_PATH

async def init_db():
    db_path = str(PROMO_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        # Основная таблица промокодов
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

async def create_promo(code: str, creator_id: int, reward_type: int, reward_value: str, duration: int, max_uses: int):
    db_path = str(PROMO_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT INTO promocodes 
            (code, creator_id, reward_type, reward_value, duration, max_uses)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (code, creator_id, reward_type, reward_value, duration, max_uses))
        await db.commit()

async def get_promo(code: str):
    db_path = str(PROMO_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT * FROM promocodes WHERE code = ?", (code,))
        row = await cursor.fetchone()
        if row:
            return {
                "code": row[0],
                "creator_id": row[1],
                "reward_type": row[2],
                "reward_value": row[3],
                "duration": row[4],
                "max_uses": row[5],
                "used_count": row[6]
            }
        return None

async def use_promo(code: str):
    db_path = str(PROMO_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?", (code,))
        await db.commit()

async def is_promo_valid(code: str) -> bool:
    promo = await get_promo(code)
    if not promo:
        return False
    return promo["used_count"] < promo["max_uses"]


async def has_user_used_promo(user_id: int, promo_code: str) -> bool:
    db_path = str(PROMO_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT 1 FROM promo_uses WHERE user_id = ? AND promo_code = ?",
            (user_id, promo_code)
        )
        return await cursor.fetchone() is not None

async def record_promo_use(user_id: int, promo_code: str):
    db_path = str(PROMO_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR IGNORE INTO promo_uses (user_id, promo_code) VALUES (?, ?)",
            (user_id, promo_code)
        )
        await db.commit()