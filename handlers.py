import asyncio
from datetime import datetime
from pyrogram import Client
from pyrogram.types import Message, CallbackQuery

from config import (AUTO_DELETE_SECONDS, BOT_NAME, BOT_VERSION,
                    ADMINS, REQUEST_CHANNEL)
from database import (
    save_file, search_files, get_languages, save_user,
    get_total_files, get_total_users, get_all_user_ids,
    get_recent_files, get_recent_users, get_top_searches,
    log_search, increment_download,
    ban_user, unban_user, is_banned, get_all_banned,
    add_request, get_pending_requests, get_user_requests,
)
from force_sub import is_subscribed, send_force_sub_message
from auto_delete import auto_delete_media
from keyboards import (
    start_keyboard, language_keyboard, quality_keyboard,
    back_home_keyboard, admin_panel_keyboard,
    broadcast_confirm_keyboard, LANGUAGE_FLAGS, QUALITY_LABELS,
)
from lang_detector import parse_movie_info

# Temporary store for broadcast message
broadcast_store = {}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


# ─────────────────────────────────────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────────────────────────────────────

async def start_handler(client: Client, message: Message):
    user       = message.from_user
    first_name = user.first_name or "Friend"
    save_user(user.id, first_name, user.username)

    await message.reply_photo(
        photo="https://telegra.ph/file/a6a27a4e35a1c3c1e8b17.jpg",
        caption=(
            f"╔══════════════════════╗\n"
            f"║   🎬 CINEMACITYHUB 🎬   ║\n"
            f"╚══════════════════════╝\n\n"
            f"👋 **Hello, {first_name}!**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🍿 **Welcome to CinemaCityHub**\n"
            f"🎥 Your Ultimate Movie Destination!\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ **Features:**\n\n"
            f"🔍 Search any movie instantly\n"
            f"🌐 Filter by language\n"
            f"📽️ Choose your quality\n"
            f"⏳ Auto-delete after timer\n"
            f"🔒 Secure force subscribe\n"
            f"🎫 Request missing movies\n"
            f"📊 Top trending movies\n"
            f"🚀 Always online 24/7\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 **Get started below!**"
        ),
        reply_markup=start_keyboard()
    )


# ─────────────────────────────────────────────────────────────────────────────
# INDEX FILES
# ─────────────────────────────────────────────────────────────────────────────

async def index_handler(client: Client, message: Message):
    media = message.document or message.video or message.audio
    if not media:
        return
    raw_name = getattr(media, "file_name", "") or "unknown"
    info     = parse_movie_info(raw_name)
    saved    = save_file(
        file_id        = media.file_id,
        file_name      = raw_name,
        file_unique_id = media.file_unique_id,
        language       = info["language"],
        quality        = info["quality"],
    )
    print(f"[{'✅ Indexed' if saved else '⚠️ Dup'}] {info['clean_name']} | {info['language']} | {info['quality']}")


# ─────────────────────────────────────────────────────────────────────────────
# MOVIE SEARCH
# ─────────────────────────────────────────────────────────────────────────────

async def filter_handler(client: Client, message: Message):
    query   = message.text.strip()
    user_id = message.from_user.id

    if not query or len(query) < 3:
        return

    if is_banned(user_id):
        await message.reply("🚫 You are banned from using CinemaCityHub.")
        return

    if not await is_subscribed(client, user_id):
        await send_force_sub_message(client, message)
        return

    log_search(query)
    languages = get_languages(query)

    if not languages:
        msg = await message.reply(
            f"❌ **No results for:** `{query}`\n\n"
            "💡 Try a shorter spelling or\n"
            "🎫 Use /request to request this movie.\n"
            "— **CinemaCityHub**"
        )
        await asyncio.sleep(10)
        for m in [msg, message]:
            try: await m.delete()
            except Exception: pass
        return

    await message.reply(
        f"🎬 **{query.title()}**\n\n"
        f"✅ Found in **{len(languages)} language(s)**\n"
        "👇 Select your preferred language:",
        reply_markup=language_keyboard(query, languages)
    )


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACKS — LANGUAGE / QUALITY / BACK
# ─────────────────────────────────────────────────────────────────────────────

async def language_callback(client: Client, cq: CallbackQuery):
    _, movie_name, language = cq.data.split("|", 2)
    results   = search_files(movie_name, language)
    if not results:
        await cq.answer("❌ No files found!", show_alert=True); return

    qualities = sorted({r.get("quality", "unknown") for r in results})
    if len(qualities) > 1:
        await cq.message.edit_text(
            f"🎬 **{movie_name.title()}**\n"
            f"🌐 Language: **{LANGUAGE_FLAGS.get(language, language.title())}**\n\n"
            "📽️ Select quality:",
            reply_markup=quality_keyboard(movie_name, language, qualities)
        )
    else:
        await cq.message.delete()
        await send_movie_files(client, cq.message, results, movie_name, language)


async def quality_callback(client: Client, cq: CallbackQuery):
    _, movie_name, language, quality = cq.data.split("|", 3)
    results  = search_files(movie_name, language)
    filtered = [r for r in results if r.get("quality") == quality]
    if not filtered:
        await cq.answer("❌ Files not found!", show_alert=True); return
    await cq.message.delete()
    await send_movie_files(client, cq.message, filtered, movie_name, language, quality)


async def back_callback(client: Client, cq: CallbackQuery):
    _, movie_name = cq.data.split("|", 1)
    languages = get_languages(movie_name)
    await cq.message.edit_text(
        f"🎬 **{movie_name.title()}** — Select language:",
        reply_markup=language_keyboard(movie_name, languages)
    )


async def back_home_callback(client: Client, cq: CallbackQuery):
    first_name = cq.from_user.first_name or "Friend"
    await cq.message.edit_caption(
        caption=(
            f"╔══════════════════════╗\n"
            f"║   🎬 CINEMACITYHUB 🎬   ║\n"
            f"╚══════════════════════╝\n\n"
            f"👋 **Hello, {first_name}!**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🍿 **Welcome to CinemaCityHub**\n"
            f"🎥 Your Ultimate Movie Destination!\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ **Features:**\n\n"
            f"🔍 Search any movie instantly\n"
            f"🌐 Filter by language\n"
            f"📽️ Choose your quality\n"
            f"⏳ Auto-delete after timer\n"
            f"🔒 Secure force subscribe\n"
            f"🎫 Request missing movies\n"
            f"📊 Top trending movies\n"
            f"🚀 Always online 24/7\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 **Get started below!**"
        ),
        reply_markup=start_keyboard()
    )


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACKS — INFO PAGES
# ─────────────────────────────────────────────────────────────────────────────

async def how_to_use_callback(client: Client, cq: CallbackQuery):
    await cq.message.edit_caption(
        caption=(
            "╔══════════════════════╗\n"
            "║      ❓ HOW TO USE      ║\n"
            "╚══════════════════════╝\n\n"
            "**Step 1️⃣** — Join our channel 📢\n\n"
            "**Step 2️⃣** — Go to our movie group 👥\n\n"
            "**Step 3️⃣** — Type the movie name 🔍\n"
            "   Example: `KGF` or `RRR` or `Pushpa`\n\n"
            "**Step 4️⃣** — Pick your language 🌐\n"
            "   Tamil | Hindi | English | Telugu...\n\n"
            "**Step 5️⃣** — Pick your quality 📽️\n"
            "   4K | 1080p | 720p | 480p\n\n"
            "**Step 6️⃣** — Download before auto-delete ⏳\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ Files delete after **{AUTO_DELETE_SECONDS // 60} minutes!**\n"
            "📥 **Save immediately!**\n\n"
            "🎫 Movie not found? Use /request"
        ),
        reply_markup=back_home_keyboard()
    )


async def about_bot_callback(client: Client, cq: CallbackQuery):
    await cq.message.edit_caption(
        caption=(
            "╔══════════════════════╗\n"
            "║  ℹ️ ABOUT CINEMACITYHUB  ║\n"
            "╚══════════════════════╝\n\n"
            f"🤖 **{BOT_NAME}** v{BOT_VERSION}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🛠️ **Built With:**\n"
            "   ⚡ Pyrogram Framework\n"
            "   🍃 MongoDB Database\n"
            "   ☁️ Render Free Hosting\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "✨ **Features:**\n"
            "   🔍 Instant movie search\n"
            "   🌐 Multi-language filter\n"
            "   📽️ Quality filter\n"
            "   ⏳ Auto-delete timer\n"
            "   🔒 Force subscribe\n"
            "   🎫 Movie request system\n"
            "   📣 Admin broadcast\n"
            "   🚫 Ban/unban users\n"
            "   📊 Stats & top searches\n"
            "   🚀 Always online 24/7\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎬 **Movies:** `{get_total_files()}`\n"
            f"👥 **Users:** `{get_total_users()}`"
        ),
        reply_markup=back_home_keyboard()
    )


async def languages_callback(client: Client, cq: CallbackQuery):
    await cq.message.edit_caption(
        caption=(
            "╔══════════════════════╗\n"
            "║  🌐 SUPPORTED LANGUAGES  ║\n"
            "╚══════════════════════╝\n\n"
            "🎭 Tamil  •  🇮🇳 Hindi\n"
            "🇺🇸 English  •  🌺 Telugu\n"
            "🌴 Malayalam  •  🌟 Kannada\n"
            "🎨 Bengali  •  🏔️ Marathi\n"
            "🌾 Punjabi  •  🔊 Dual Audio\n"
            "🌐 Multi Audio\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 More languages added regularly!"
        ),
        reply_markup=back_home_keyboard()
    )


async def qualities_callback(client: Client, cq: CallbackQuery):
    await cq.message.edit_caption(
        caption=(
            "╔══════════════════════╗\n"
            "║   📽️ VIDEO QUALITIES    ║\n"
            "╚══════════════════════╝\n\n"
            "🔵 **4K UHD** — Ultra HD 2160p\n\n"
            "🟢 **1080p FHD** — Full HD\n\n"
            "🟡 **720p HD** — High Definition\n\n"
            "🟠 **480p SD** — Standard\n\n"
            "🔴 **360p CAM** — Low Quality\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Availability depends on uploads!"
        ),
        reply_markup=back_home_keyboard()
    )


async def top_movies_callback(client: Client, cq: CallbackQuery):
    top = get_top_searches(10)
    if not top:
        await cq.answer("No search data yet!", show_alert=True); return
    text = "╔══════════════════════╗\n║  🔝 TOP SEARCHED MOVIES  ║\n╚══════════════════════╝\n\n"
    for i, item in enumerate(top, 1):
        text += f"{i}. 🎬 **{item['movie_name'].title()}** — `{item['count']}` searches\n"
    text += "\n━━━━━━━━━━━━━━━━━━━━━\n🔍 Search any movie above!"
    await cq.message.edit_caption(caption=text, reply_markup=back_home_keyboard())


async def request_info_callback(client: Client, cq: CallbackQuery):
    await cq.message.edit_caption(
        caption=(
            "╔══════════════════════╗\n"
            "║    🎫 MOVIE REQUEST     ║\n"
            "╚══════════════════════╝\n\n"
            "Can't find your movie? Request it!\n\n"
            "**How to request:**\n\n"
            "Send this command in the bot:\n"
            "`/request Movie Name`\n\n"
            "**Example:**\n"
            "`/request Leo Tamil 1080p`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "⏳ Admins will upload within 24 hours.\n"
            "You'll get notified when it's ready!"
        ),
        reply_markup=back_home_keyboard()
    )


# ─────────────────────────────────────────────────────────────────────────────
# MOVIE REQUEST COMMAND
# ─────────────────────────────────────────────────────────────────────────────

async def request_handler(client: Client, message: Message):
    user = message.from_user
    args = message.text.split(None, 1)

    if len(args) < 2:
        await message.reply(
            "❌ **Usage:** `/request Movie Name`\n\n"
            "**Example:** `/request Leo Tamil 1080p`"
        )
        return

    movie_name = args[1].strip()
    add_request(user.id, user.username or "unknown", movie_name)

    # Notify request channel if set
    if REQUEST_CHANNEL:
        try:
            await client.send_message(
                REQUEST_CHANNEL,
                f"🎫 **New Movie Request**\n\n"
                f"🎬 Movie: **{movie_name}**\n"
                f"👤 User: [{user.first_name}](tg://user?id={user.id})\n"
                f"🆔 ID: `{user.id}`\n"
                f"📅 Time: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC`"
            )
        except Exception:
            pass

    await message.reply(
        f"✅ **Request Submitted!**\n\n"
        f"🎬 Movie: **{movie_name}**\n\n"
        "⏳ Admins will upload within 24 hours.\n"
        "You'll be notified when it's ready!\n"
        "— **CinemaCityHub**"
    )


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────────────────────────────────────

async def admin_handler(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply("❌ You are not an admin."); return

    await message.reply(
        "╔══════════════════════╗\n"
        "║    🛠️ ADMIN PANEL      ║\n"
        "╚══════════════════════╝\n\n"
        f"👋 Welcome, **{message.from_user.first_name}**!\n\n"
        f"🎬 Files: `{get_total_files()}`\n"
        f"👥 Users: `{get_total_users()}`\n\n"
        "Select an option below:",
        reply_markup=admin_panel_keyboard()
    )


async def admin_stats_callback(client: Client, cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        await cq.answer("❌ Not an admin!", show_alert=True); return
    recent_users = get_recent_users(3)
    recent_files = get_recent_files(3)
    u_text = "\n".join([f"  • {u.get('first_name','?')} (`{u['user_id']}`)" for u in recent_users]) or "  None"
    f_text = "\n".join([f"  • {parse_movie_info(f['file_name'])['clean_name']}" for f in recent_files]) or "  None"
    await cq.message.edit_text(
        "📊 **CinemaCityHub Stats**\n\n"
        f"🎬 Total Files: `{get_total_files()}`\n"
        f"👥 Total Users: `{get_total_users()}`\n"
        f"🚫 Banned: `{len(get_all_banned())}`\n"
        f"🎫 Requests: `{len(get_pending_requests())}`\n\n"
        "👤 **Recent Users:**\n" + u_text + "\n\n"
        "🎞️ **Recent Files:**\n" + f_text,
        reply_markup=admin_panel_keyboard()
    )


async def admin_top_callback(client: Client, cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        await cq.answer("❌ Not an admin!", show_alert=True); return
    top = get_top_searches(10)
    text = "🔝 **Top Searches**\n\n"
    for i, item in enumerate(top, 1):
        text += f"{i}. **{item['movie_name'].title()}** — `{item['count']}`\n"
    if not top:
        text += "No data yet."
    await cq.message.edit_text(text, reply_markup=admin_panel_keyboard())


async def admin_requests_callback(client: Client, cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        await cq.answer("❌ Not an admin!", show_alert=True); return
    reqs = get_pending_requests()
    if not reqs:
        await cq.answer("No pending requests!", show_alert=True); return
    text = f"🎫 **Pending Requests ({len(reqs)})**\n\n"
    for r in reqs[:10]:
        text += (f"🎬 **{r['movie_name']}**\n"
                 f"   👤 @{r.get('username','?')} | 🆔 `{r['user_id']}`\n"
                 f"   📅 {r['requested_on'].strftime('%d %b %Y')}\n\n")
    await cq.message.edit_text(text, reply_markup=admin_panel_keyboard())


async def admin_banned_callback(client: Client, cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        await cq.answer("❌ Not an admin!", show_alert=True); return
    banned = get_all_banned()
    if not banned:
        await cq.answer("No banned users!", show_alert=True); return
    text = f"🚫 **Banned Users ({len(banned)})**\n\n"
    for b in banned[:10]:
        text += f"🆔 `{b['user_id']}` — {b.get('reason','No reason')}\n"
    await cq.message.edit_text(text, reply_markup=admin_panel_keyboard())


async def admin_deleteall_callback(client: Client, cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        await cq.answer("❌ Not an admin!", show_alert=True); return
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await cq.message.edit_text(
        "⚠️ **Delete ALL indexed files?**\n\n"
        "This cannot be undone!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Delete All", callback_data="confirm_deleteall"),
             InlineKeyboardButton("❌ Cancel",          callback_data="admin_close")],
        ])
    )


async def confirm_deleteall_callback(client: Client, cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        await cq.answer("❌ Not an admin!", show_alert=True); return
    from database import delete_all_files
    delete_all_files()
    await cq.message.edit_text(
        "🗑️ **All files deleted successfully.**",
        reply_markup=admin_panel_keyboard()
    )


async def admin_close_callback(client: Client, cq: CallbackQuery):
    try:
        await cq.message.delete()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# BROADCAST
# ─────────────────────────────────────────────────────────────────────────────

async def admin_broadcast_callback(client: Client, cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        await cq.answer("❌ Not an admin!", show_alert=True); return
    broadcast_store[cq.from_user.id] = {"step": "waiting"}
    await cq.message.edit_text(
        "📣 **Broadcast Message**\n\n"
        "Send the message you want to broadcast to all users.\n"
        "_(Text, photo, or video)_\n\n"
        "Send /cancel to cancel.",
    )


async def handle_broadcast_input(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    if user_id not in broadcast_store:
        return
    if broadcast_store[user_id].get("step") != "waiting":
        return

    broadcast_store[user_id] = {"step": "confirm", "message": message}
    await message.reply(
        f"📣 **Confirm Broadcast**\n\n"
        f"Send to **{get_total_users()} users**?\n\n"
        "Tap ✅ Yes to confirm or ❌ Cancel.",
        reply_markup=broadcast_confirm_keyboard()
    )


async def broadcast_confirm_callback(client: Client, cq: CallbackQuery):
    user_id = cq.from_user.id
    if not is_admin(user_id):
        await cq.answer("❌ Not an admin!", show_alert=True); return

    data = broadcast_store.get(user_id, {})
    msg  = data.get("message")
    if not msg:
        await cq.answer("No message found!", show_alert=True); return

    user_ids = get_all_user_ids()
    success, fail = 0, 0

    await cq.message.edit_text(f"📣 Broadcasting to {len(user_ids)} users...")

    for uid in user_ids:
        try:
            if msg.text:
                await client.send_message(uid, msg.text)
            elif msg.photo:
                await client.send_photo(uid, msg.photo.file_id, caption=msg.caption or "")
            elif msg.video:
                await client.send_video(uid, msg.video.file_id, caption=msg.caption or "")
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1

    broadcast_store.pop(user_id, None)
    await cq.message.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"✅ Sent: `{success}`\n"
        f"❌ Failed: `{fail}`\n"
        f"👥 Total: `{len(user_ids)}`",
        reply_markup=admin_panel_keyboard()
    )


# ─────────────────────────────────────────────────────────────────────────────
# BAN / UNBAN COMMANDS
# ─────────────────────────────────────────────────────────────────────────────

async def ban_handler(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Not an admin."); return
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /ban <user_id> [reason]"); return
    try:
        uid    = int(args[1])
        reason = " ".join(args[2:]) if len(args) > 2 else "No reason"
        ban_user(uid, reason)
        await message.reply(f"🚫 User `{uid}` banned.\nReason: {reason}")
        try:
            await client.send_message(uid,
                f"🚫 You have been banned from **CinemaCityHub**.\n"
                f"Reason: {reason}")
        except Exception:
            pass
    except ValueError:
        await message.reply("❌ Invalid user ID.")


async def unban_handler(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Not an admin."); return
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /unban <user_id>"); return
    try:
        uid = int(args[1])
        unban_user(uid)
        await message.reply(f"✅ User `{uid}` unbanned.")
        try:
            await client.send_message(uid,
                "✅ You have been **unbanned** from CinemaCityHub!\n"
                "You can now search for movies again.")
        except Exception:
            pass
    except ValueError:
        await message.reply("❌ Invalid user ID.")


# ─────────────────────────────────────────────────────────────────────────────
# SEND MOVIE FILES + AUTO DELETE
# ─────────────────────────────────────────────────────────────────────────────

async def send_movie_files(client, message, results,
                           movie_name, language, quality=None):
    chat_id   = message.chat.id
    sent_msgs = []

    lang_label = (LANGUAGE_FLAGS.get(language, language.title())
                  if language != "all" else "🌍 All Languages")
    q_label    = (f" • {QUALITY_LABELS.get(quality, quality.upper())}"
                  if quality and quality != "unknown" else "")

    header = await client.send_message(
        chat_id,
        f"🎬 **{movie_name.title()}**\n"
        f"🌐 Language: **{lang_label}**{q_label}\n"
        f"📦 Files: **{len(results)}**\n\n"
        f"⚠️ Auto-delete in **{AUTO_DELETE_SECONDS // 60} min** — save now!\n"
        "— **CinemaCityHub**"
    )
    sent_msgs.append(header)

    for movie in results:
        try:
            info = parse_movie_info(movie["file_name"])
            sent = await client.send_cached_media(
                chat_id = chat_id,
                file_id = movie["file_id"],
                caption = (
                    f"🎞️ **{info['clean_name']}**\n"
                    f"🌐 {movie.get('language','?').title()} "
                    f"| 📽️ {movie.get('quality','?').upper()}\n"
                    f"🗑️ Auto-deletes in {AUTO_DELETE_SECONDS // 60}m\n"
                    "— **CinemaCityHub**"
                )
            )
            sent_msgs.append(sent)
            increment_download(movie["file_unique_id"])
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"[ERROR] {movie.get('file_name','?')}: {e}")

    notice = await client.send_message(
        chat_id,
        f"⏳ **Auto-Delete Timer Started**\n\n"
        f"Files delete in **{AUTO_DELETE_SECONDS // 60} minutes**.\n"
        "📥 Save them now!\n"
        "— **CinemaCityHub**"
    )
    asyncio.create_task(auto_delete_media(client, sent_msgs, notice))
