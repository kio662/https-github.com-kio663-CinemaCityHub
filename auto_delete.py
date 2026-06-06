import asyncio
from pyrogram.errors import MessageDeleteForbidden, FloodWait
from config import AUTO_DELETE_SECONDS


async def auto_delete_media(client, sent_messages: list, notice_message):
    total       = AUTO_DELETE_SECONDS
    checkpoints = sorted({t for t in [total, total // 2, 60, 30, 10] if 0 < t < total}, reverse=True)
    elapsed     = 0

    for cp in checkpoints:
        wait = (total - cp) - elapsed
        if wait > 0:
            await asyncio.sleep(wait)
            elapsed += wait
        mins, secs = divmod(cp, 60)
        time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
        try:
            await notice_message.edit_text(
                "⚠️ **CinemaCityHub — Auto Delete**\n\n"
                f"🗑️ Files delete in **{time_str}**\n"
                "📥 **Save them before they're gone!**"
            )
        except Exception:
            pass

    remaining = total - elapsed - (checkpoints[-1] if checkpoints else 0)
    if remaining > 0:
        await asyncio.sleep(remaining)

    for msg in sent_messages:
        try:
            await msg.delete()
        except MessageDeleteForbidden:
            pass
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            pass

    try:
        await notice_message.edit_text(
            "🗑️ **Files have been deleted.**\n\n"
            "🔍 Search again any time.\n"
            "— **CinemaCityHub**"
        )
    except Exception:
        pass

    await asyncio.sleep(30)
    try:
        await notice_message.delete()
    except Exception:
        pass
