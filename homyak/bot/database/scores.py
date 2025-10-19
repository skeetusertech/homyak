import aiosqlite
from ..config import SCORES_DB_PATH, CARDS_DB_PATH

async def init_db():
    db_path = str(SCORES_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_scores (
                user_id INTEGER PRIMARY KEY,
                total_score INTEGER NOT NULL DEFAULT 0,
                last_homyak TEXT
            )
        """)

        cursor = await db.execute("PRAGMA table_info(user_scores)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "last_homyak" not in column_names:
            await db.execute("ALTER TABLE user_scores ADD COLUMN last_homyak TEXT")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_user_scores (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                total_score INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            )
        """)

        await db.commit()

async def add_score(user_id: int, points: int, homyak_name: str = None, chat_id: int | None = None):
    db_path = str(SCORES_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        if homyak_name:
            await db.execute("""
                INSERT INTO user_scores (user_id, total_score, last_homyak)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET 
                    total_score = total_score + excluded.total_score,
                    last_homyak = excluded.last_homyak
            """, (user_id, points, homyak_name))
        else:
            await db.execute("""
                INSERT INTO user_scores (user_id, total_score)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET total_score = total_score + excluded.total_score
            """, (user_id, points))

        if chat_id is not None:
            await db.execute("""
                INSERT INTO chat_user_scores (chat_id, user_id, total_score)
                VALUES (?, ?, ?)
                ON CONFLICT(chat_id, user_id) DO UPDATE SET
                    total_score = total_score + excluded.total_score
            """, (chat_id, user_id, points))

        await db.commit()

async def get_score(user_id: int) -> tuple[int, str | None]:
    db_path = str(SCORES_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT total_score, last_homyak FROM user_scores WHERE user_id = ?", 
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0], row[1]
        return 0, None
    
async def get_top_scores_in_chat(chat_id: int, limit: int = 10):
    db_path = str(SCORES_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("""
            SELECT user_id, total_score FROM chat_user_scores
            WHERE chat_id = ?
            ORDER BY total_score DESC
            LIMIT ?
        """, (chat_id, limit))
        score_rows = await cursor.fetchall()

        if not score_rows:
            cursor = await db.execute("""
                SELECT user_id, total_score FROM user_scores
                ORDER BY total_score DESC
                LIMIT ?
            """, (limit,))
            score_rows = await cursor.fetchall()

    if not score_rows:
        return []

    from bot.main import bot
    top_list = []
    for user_id, score in score_rows:
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status not in ["left", "kicked"]:
                user = member.user
                first_name = user.first_name or ""
                username = user.username
                top_list.append((user_id, score, first_name, username))
                if len(top_list) >= limit:
                    break
        except:
            continue

    return top_list

async def get_all_cards_in_chat(chat_id: int):
    from bot.main import bot
    db_path = str(CARDS_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("""
            SELECT user_id, COUNT(*) as card_count
            FROM user_cards
            GROUP BY user_id
        """)
        rows = await cursor.fetchall()
    
    valid_users = []
    for user_id, count in rows:
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status not in ["left", "kicked"]:
                valid_users.append((user_id, count))
        except:
            continue
    return valid_users

async def get_all_user_ids_with_scores():
    db_path = str(SCORES_DB_PATH)
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT user_id FROM user_scores")
        return [row[0] for row in await cursor.fetchall()]