import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).parent.parent

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
DATABASE_PATH = "users.db"
SETTINGS = {"GLOBAL_COOLDOWN_MINUTES": 420}
WELCOME_VIDEO_PATH = BASE_DIR / "files" / "welcome.mp4"
HOMYAK_FILES_DIR = BASE_DIR / "bot" / "files"
USERS_DB_PATH = BASE_DIR / "data" / "users.db"
COOLDOWN_DB_PATH = BASE_DIR / "data" / "cooldowns.db"
ADMINS_DB_PATH = BASE_DIR / "data" / "admins.db"
RARITY_DB_PATH = BASE_DIR / "data" / "rarity.db"
SCORES_DB_PATH = BASE_DIR / "data" / "scores.db"
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN")
PREMIUM_DB_PATH = BASE_DIR / "data" / "premium.db"
BONUS_CHANNEL_ID = "@homyakadventcl"
CARDS_DB_PATH = BASE_DIR / "data" / "cards.db"
PROMO_DB_PATH = BASE_DIR / "data" / "promo.db"
BONUS_DB_PATH = BASE_DIR / "data" / "bonuses.db"