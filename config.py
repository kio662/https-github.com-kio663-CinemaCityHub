import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────────────────────────────
API_ID              = int(os.getenv("API_ID", "0"))
API_HASH            = os.getenv("API_HASH", "")
BOT_TOKEN           = os.getenv("BOT_TOKEN", "")

# ── MongoDB ───────────────────────────────────────────────────────────────────
MONGO_URI           = os.getenv("MONGO_URI", "")

# ── Channels ──────────────────────────────────────────────────────────────────
DB_CHANNEL          = int(os.getenv("DB_CHANNEL", "0"))
FORCE_SUB_CHANNEL   = int(os.getenv("FORCE_SUB_CHANNEL", "0"))
FORCE_SUB_INVITE    = os.getenv("FORCE_SUB_INVITE", "https://t.me/your_channel")

# ── Admins ────────────────────────────────────────────────────────────────────
# Comma-separated list of admin user IDs e.g. "123456,789012"
ADMINS              = [int(x) for x in os.getenv("ADMINS", "0").split(",") if x.strip().isdigit()]

# ── Settings ──────────────────────────────────────────────────────────────────
AUTO_DELETE_SECONDS = int(os.getenv("AUTO_DELETE_SECONDS", "300"))
RENDER_URL          = os.getenv("RENDER_URL", "")
MAX_RESULTS         = int(os.getenv("MAX_RESULTS", "10"))
REQUEST_CHANNEL     = int(os.getenv("REQUEST_CHANNEL", "0"))   # channel for movie requests

# ── Bot Info ──────────────────────────────────────────────────────────────────
BOT_NAME            = "CinemaCityHub"
BOT_USERNAME        = os.getenv("BOT_USERNAME", "CinemaCityHubBot")
BOT_VERSION         = "3.0"
SUPPORT_URL         = os.getenv("SUPPORT_URL", "https://t.me/your_group")
CHANNEL_URL         = os.getenv("CHANNEL_URL", "https://t.me/your_channel")
