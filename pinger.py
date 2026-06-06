import asyncio
import aiohttp
from config import RENDER_URL


async def self_ping():
    if not RENDER_URL:
        print("[PINGER] RENDER_URL not set — disabled.")
        return
    await asyncio.sleep(60)
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{RENDER_URL}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    print(f"[PINGER] ping → {resp.status}")
        except Exception as e:
            print(f"[PINGER] failed: {e}")
        await asyncio.sleep(600)
