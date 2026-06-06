import asyncio
import threading

# ── Fix: create event loop before pyrogram imports (Python 3.10+ compatibility)
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from config import API_ID, API_HASH, BOT_TOKEN, DB_CHANNEL, ADMINS, BOT_VERSION, RENDER_URL
from keep_alive import run_keep_alive
from pinger import self_ping
from handlers import (
    start_handler, index_handler, filter_handler,
    language_callback, quality_callback, back_callback,
    back_home_callback, how_to_use_callback, about_bot_callback,
    languages_callback, qualities_callback,
    top_movies_callback, request_info_callback,
    request_handler,
    admin_handler, admin_stats_callback, admin_top_callback,
    admin_requests_callback, admin_banned_callback,
    admin_deleteall_callback, confirm_deleteall_callback,
    admin_close_callback,
    admin_broadcast_callback, handle_broadcast_input,
    broadcast_confirm_callback,
    ban_handler, unban_handler,
    broadcast_store,
)
from force_sub import is_subscribed
from database import get_total_files, get_total_users

# ─────────────────────────────────────────────────────────────────────────────
# Client
# ─────────────────────────────────────────────────────────────────────────────

app = Client(
    "cinemacityhub",
    api_id    = API_ID,
    api_hash  = API_HASH,
    bot_token = BOT_TOKEN,
)


# ─────────────────────────────────────────────────────────────────────────────
# COMMANDS
# ─────────────────────────────────────────────────────────────────────────────

@app.on_message(filters.command("start"))
async def cmd_start(client: Client, message: Message):
    await start_handler(client, message)


@app.on_message(filters.command("help"))
async def cmd_help(client: Client, message: Message):
    await message.reply(
        "╔══════════════════════╗\n"
        "║   🎬 CINEMACITYHUB    ║\n"
        "╚══════════════════════╝\n\n"
        "**User Commands:**\n\n"
        "/start — Welcome screen\n"
        "/request <movie> — Request a movie\n"
        "/myrequests — View your requests\n"
        "/ping — Check bot status\n"
        "/help — This message\n\n"
        "**Admin Commands:**\n\n"
        "/admin — Open admin panel\n"
        "/ban <id> [reason] — Ban user\n"
        "/unban <id> — Unban user\n"
        "/stats — Quick stats\n\n"
        "**How to search:**\n"
        "Just type any movie name in the group!\n\n"
        "— **CinemaCityHub**"
    )


@app.on_message(filters.command("ping"))
async def cmd_ping(client: Client, message: Message):
    await message.reply("🏓 Pong! CinemaCityHub is alive.")


@app.on_message(filters.command("status"))
async def cmd_status(client: Client, message: Message):
    await message.reply(
        "✅ **CinemaCityHub Status**\n\n"
        f"🤖 Version: **{BOT_VERSION}**\n"
        f"☁️ Server: Render Free Tier\n"
        f"🌐 URL: `{RENDER_URL or 'Not set'}`\n"
        f"🎬 Files: `{get_total_files()}`\n"
        f"👥 Users: `{get_total_users()}`\n"
        "🔄 Self-ping: Every 10 min"
    )


@app.on_message(filters.command("stats"))
async def cmd_stats(client: Client, message: Message):
    if message.from_user.id not in ADMINS:
        await message.reply("❌ Admin only."); return
    await message.reply(
        f"📊 **Quick Stats**\n\n"
        f"🎬 Files: `{get_total_files()}`\n"
        f"👥 Users: `{get_total_users()}`"
    )


@app.on_message(filters.command("request"))
async def cmd_request(client: Client, message: Message):
    await request_handler(client, message)


@app.on_message(filters.command("myrequests"))
async def cmd_myrequests(client: Client, message: Message):
    reqs = get_user_requests(message.from_user.id)
    if not reqs:
        await message.reply("You haven't made any requests yet.\nUse /request Movie Name"); return
    text = "🎫 **Your Requests:**\n\n"
    for r in reqs:
        status_icon = {"pending": "⏳", "done": "✅", "rejected": "❌"}.get(r["status"], "❓")
        text += f"{status_icon} **{r['movie_name']}** — {r['status'].title()}\n"
    await message.reply(text)


@app.on_message(filters.command("admin"))
async def cmd_admin(client: Client, message: Message):
    await admin_handler(client, message)


@app.on_message(filters.command("ban"))
async def cmd_ban(client: Client, message: Message):
    await ban_handler(client, message)


@app.on_message(filters.command("unban"))
async def cmd_unban(client: Client, message: Message):
    await unban_handler(client, message)


@app.on_message(filters.command("cancel") & filters.private)
async def cmd_cancel(client: Client, message: Message):
    broadcast_store.pop(message.from_user.id, None)
    await message.reply("❌ Cancelled.")


# ─────────────────────────────────────────────────────────────────────────────
# AUTO-INDEX DB CHANNEL
# ─────────────────────────────────────────────────────────────────────────────

@app.on_message(filters.channel & filters.chat(DB_CHANNEL))
async def auto_index(client: Client, message: Message):
    await index_handler(client, message)


# ─────────────────────────────────────────────────────────────────────────────
# BROADCAST INPUT (admin private message)
# ─────────────────────────────────────────────────────────────────────────────

@app.on_message(
    filters.private
    & filters.user(ADMINS)
    & ~filters.command(["start", "help", "ping", "status", "stats",
                        "request", "myrequests", "admin", "ban", "unban", "cancel"])
)
async def admin_input(client: Client, message: Message):
    if message.from_user.id in broadcast_store:
        await handle_broadcast_input(client, message)


# ─────────────────────────────────────────────────────────────────────────────
# GROUP SEARCH
# ─────────────────────────────────────────────────────────────────────────────

@app.on_message(
    filters.group & filters.text
    & ~filters.command(["start", "help", "ping", "status",
                        "request", "myrequests", "admin", "ban", "unban"])
)
async def search_movie(client: Client, message: Message):
    await filter_handler(client, message)


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK QUERIES
# ─────────────────────────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex(r"^lang\|"))
async def on_language(client, cq): await language_callback(client, cq)

@app.on_callback_query(filters.regex(r"^quality\|"))
async def on_quality(client, cq): await quality_callback(client, cq)

@app.on_callback_query(filters.regex(r"^back\|"))
async def on_back(client, cq): await back_callback(client, cq)

@app.on_callback_query(filters.regex("^back_home$"))
async def on_back_home(client, cq): await back_home_callback(client, cq)

@app.on_callback_query(filters.regex("^how_to_use$"))
async def on_how_to_use(client, cq): await how_to_use_callback(client, cq)

@app.on_callback_query(filters.regex("^about_bot$"))
async def on_about(client, cq): await about_bot_callback(client, cq)

@app.on_callback_query(filters.regex("^languages$"))
async def on_languages(client, cq): await languages_callback(client, cq)

@app.on_callback_query(filters.regex("^qualities$"))
async def on_qualities(client, cq): await qualities_callback(client, cq)

@app.on_callback_query(filters.regex("^top_movies$"))
async def on_top(client, cq): await top_movies_callback(client, cq)

@app.on_callback_query(filters.regex("^request_info$"))
async def on_req_info(client, cq): await request_info_callback(client, cq)

@app.on_callback_query(filters.regex("^admin_stats$"))
async def on_admin_stats(client, cq): await admin_stats_callback(client, cq)

@app.on_callback_query(filters.regex("^admin_files$"))
async def on_admin_files(client, cq):
    if cq.from_user.id not in ADMINS:
        await cq.answer("❌ Not an admin!", show_alert=True); return
    recent = get_recent_files(10)
    text   = f"📁 **Total Files: {get_total_files()}**\n\n**Recent Additions:**\n"
    for f in recent:
        info = parse_movie_info(f["file_name"])
        text += f"🎬 {info['clean_name']} | {f.get('language','?')} | {f.get('quality','?')}\n"
    from handlers import parse_movie_info
    await cq.message.edit_text(text, reply_markup=admin_panel_keyboard())

@app.on_callback_query(filters.regex("^admin_users$"))
async def on_admin_users(client, cq):
    if cq.from_user.id not in ADMINS:
        await cq.answer("❌ Not an admin!", show_alert=True); return
    recent = get_recent_users(10)
    text   = f"👥 **Total Users: {get_total_users()}**\n\n**Recent Users:**\n"
    for u in recent:
        text += f"👤 {u.get('first_name','?')} | ID: `{u['user_id']}`\n"
    await cq.message.edit_text(text, reply_markup=admin_panel_keyboard())

@app.on_callback_query(filters.regex("^admin_top$"))
async def on_admin_top(client, cq): await admin_top_callback(client, cq)

@app.on_callback_query(filters.regex("^admin_requests$"))
async def on_admin_requests(client, cq): await admin_requests_callback(client, cq)

@app.on_callback_query(filters.regex("^admin_banned$"))
async def on_admin_banned(client, cq): await admin_banned_callback(client, cq)

@app.on_callback_query(filters.regex("^admin_broadcast$"))
async def on_admin_broadcast(client, cq): await admin_broadcast_callback(client, cq)

@app.on_callback_query(filters.regex("^broadcast_confirm$"))
async def on_broadcast_confirm(client, cq): await broadcast_confirm_callback(client, cq)

@app.on_callback_query(filters.regex("^admin_deleteall$"))
async def on_admin_deleteall(client, cq): await admin_deleteall_callback(client, cq)

@app.on_callback_query(filters.regex("^confirm_deleteall$"))
async def on_confirm_deleteall(client, cq): await confirm_deleteall_callback(client, cq)

@app.on_callback_query(filters.regex("^admin_close$"))
async def on_admin_close(client, cq): await admin_close_callback(client, cq)

@app.on_callback_query(filters.regex("^check_sub$"))
async def on_check_sub(client, cq):
    if await is_subscribed(client, cq.from_user.id):
        await cq.message.delete()
        await cq.answer("✅ Verified! Search for a movie now.", show_alert=True)
    else:
        await cq.answer("❌ Please join the channel first!", show_alert=True)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    threading.Thread(target=run_keep_alive, daemon=True).start()
    asyncio.create_task(self_ping())

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  🎬  CinemaCityHub v" + BOT_VERSION + " Starting...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    await app.start()
    me = await app.get_me()

    print(f"  ✅  Bot: @{me.username}")
    print(f"  🎬  Files: {get_total_files()}")
    print(f"  👥  Users: {get_total_users()}")
    print(f"  🌐  Keep-alive: port 8080")
    print(f"  🔄  Self-ping: {RENDER_URL or 'disabled'}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
