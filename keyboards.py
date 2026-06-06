from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CHANNEL_URL, SUPPORT_URL, BOT_USERNAME

LANGUAGE_FLAGS = {
    "tamil":     "🎭 Tamil",
    "hindi":     "🇮🇳 Hindi",
    "english":   "🇺🇸 English",
    "telugu":    "🌺 Telugu",
    "malayalam": "🌴 Malayalam",
    "kannada":   "🌟 Kannada",
    "bengali":   "🎨 Bengali",
    "marathi":   "🏔️ Marathi",
    "punjabi":   "🌾 Punjabi",
    "dual":      "🔊 Dual Audio",
    "multi":     "🌐 Multi Audio",
    "unknown":   "🎬 Unknown",
}

QUALITY_LABELS = {
    "4k":      "🔵 4K UHD",
    "1080p":   "🟢 1080p FHD",
    "720p":    "🟡 720p HD",
    "480p":    "🟠 480p SD",
    "360p":    "🔴 360p CAM",
    "unknown": "❓ Unknown",
}


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Search Movie", switch_inline_query_current_chat="")],
        [InlineKeyboardButton("📢 Updates Channel", url=CHANNEL_URL),
         InlineKeyboardButton("👥 Support Group",   url=SUPPORT_URL)],
        [InlineKeyboardButton("❓ How to use",   callback_data="how_to_use"),
         InlineKeyboardButton("ℹ️ About bot",    callback_data="about_bot")],
        [InlineKeyboardButton("🌐 Languages",    callback_data="languages"),
         InlineKeyboardButton("📽️ Qualities",   callback_data="qualities")],
        [InlineKeyboardButton("🎫 Request Movie", callback_data="request_info"),
         InlineKeyboardButton("📊 Top Movies",   callback_data="top_movies")],
        [InlineKeyboardButton(
            "🚀 Share CinemaCityHub",
            url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}"
                f"&text=🎬 Best Movie Bot!")],
    ])


def language_keyboard(movie_name: str, languages: list) -> InlineKeyboardMarkup:
    buttons, row = [], []
    for lang in languages:
        label = LANGUAGE_FLAGS.get(lang, f"🎬 {lang.title()}")
        row.append(InlineKeyboardButton(label, callback_data=f"lang|{movie_name[:30]}|{lang}"))
        if len(row) == 2:
            buttons.append(row); row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🌍 All Languages", callback_data=f"lang|{movie_name[:30]}|all")])
    return InlineKeyboardMarkup(buttons)


def quality_keyboard(movie_name: str, language: str, qualities: list) -> InlineKeyboardMarkup:
    buttons, row = [], []
    for q in qualities:
        label = QUALITY_LABELS.get(q, f"📽️ {q.upper()}")
        row.append(InlineKeyboardButton(label, callback_data=f"quality|{movie_name[:25]}|{language}|{q}"))
        if len(row) == 2:
            buttons.append(row); row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"back|{movie_name[:30]}")])
    return InlineKeyboardMarkup(buttons)


def back_home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Back to home", callback_data="back_home")]])


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Full Stats",      callback_data="admin_stats"),
         InlineKeyboardButton("📁 Total Files",     callback_data="admin_files")],
        [InlineKeyboardButton("👥 Users List",      callback_data="admin_users"),
         InlineKeyboardButton("🔝 Top Searches",    callback_data="admin_top")],
        [InlineKeyboardButton("🎫 Requests",        callback_data="admin_requests"),
         InlineKeyboardButton("🚫 Banned Users",    callback_data="admin_banned")],
        [InlineKeyboardButton("📣 Broadcast",       callback_data="admin_broadcast"),
         InlineKeyboardButton("🗑️ Delete All Files", callback_data="admin_deleteall")],
        [InlineKeyboardButton("🏠 Close Panel",     callback_data="admin_close")],
    ])


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes, Send",  callback_data="broadcast_confirm"),
         InlineKeyboardButton("❌ Cancel",     callback_data="admin_close")],
    ])
