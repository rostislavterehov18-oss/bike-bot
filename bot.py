from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import asyncio
import json
import os

# =========================
# CONFIG
# =========================

TOKEN = "8793663575:AAHSXPQIT16ZLn9ycLzwcQI3pWg0sdyfcwU"
CHAT_ID = 5449343705  # твой Telegram ID

seen_file = "seen_items.json"

# =========================
# LOAD SEEN
# =========================

if os.path.exists(seen_file):
    try:
        with open(seen_file, "r", encoding="utf-8") as f:
            seen = set(json.load(f))
    except:
        seen = set()
else:
    seen = set()


def save_seen():
    with open(seen_file, "w", encoding="utf-8") as f:
        json.dump(list(seen), f)


# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚲 Бот работает!\n\n"
        "Ищу велосипеды 0–200 CHF каждые 15 минут."
    )


# =========================
# TUTTI SEARCH
# =========================

def search_tutti():
    url = "https://www.tutti.ch/api/v10/search"

    params = {
        "query": "velo bike fahrrad",
        "priceFrom": 0,
        "priceTo": 200,
        "limit": 20
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=20)
        if r.status_code != 200:
            return []

        data = r.json()
        results = []

        for item in data.get("items", []):
            title = item.get("title", "no title")
            link = "https://www.tutti.ch" + item.get("url", "")

            if link not in seen:
                seen.add(link)
                results.append((title[:100], link))

        return results

    except:
        return []


# =========================
# RICARDO SEARCH
# =========================

def search_ricardo():
    url = "https://www.ricardo.ch/api/search/v1/search"

    params = {
        "query": "velo bike",
        "priceFrom": 0,
        "priceTo": 200,
        "limit": 20
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=20)
        if r.status_code != 200:
            return []

        data = r.json()
        results = []

        for item in data.get("items", []):
            title = item.get("title", "no title")
            link = item.get("url", "")

            if not link.startswith("http"):
                link = "https://www.ricardo.ch" + link

            if link not in seen:
                seen.add(link)
                results.append((title[:100], link))

        return results

    except:
        return []


# =========================
# SEARCH ALL
# =========================

async def search_all():
    results = []
    results += search_tutti()
    results += search_ricardo()

    save_seen()
    return results


# =========================
# LOOP
# =========================

async def loop(app: Application):
    while True:
        try:
            items = await search_all()

            if items:
                msg = "🚲 Новые велосипеды 0–200 CHF:\n\n"

                for title, link in items:
                    msg += f"{title}\n{link}\n\n"

                await app.bot.send_message(chat_id=CHAT_ID, text=msg)

            print("Loop OK")

        except Exception as e:
            print("Loop error:", e)

        await asyncio.sleep(900)


# =========================
# START LOOP
# =========================

async def post_init(app: Application):
    asyncio.create_task(loop(app))


# =========================
# MAIN
# =========================

def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))

    print("🚲 Bot started")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
