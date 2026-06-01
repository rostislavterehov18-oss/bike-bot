from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import asyncio
import json
import os

TOKEN = "8793663575:AAENYY0AMKjd3dXZlKX_uwrlEWgRDmAFIPU"

CHAT_ID = None

seen_file = "seen_items.json"

# -------------------------
# LOAD SEEN FROM FILE (чтобы не повторял после перезапуска)
# -------------------------
if os.path.exists(seen_file):
    with open(seen_file, "r", encoding="utf-8") as f:
        seen = set(json.load(f))
else:
    seen = set()


def save_seen():
    with open(seen_file, "w", encoding="utf-8") as f:
        json.dump(list(seen), f)


# -------------------------
# START
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.effective_chat.id

    await update.message.reply_text(
        "🚲 Бот активирован!\n\nИщу велосипеды 0–200 CHF каждые 15 минут.\nСтарые объявления игнорируются."
    )


# -------------------------
# TUTTI SEARCH
# -------------------------
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
            url_item = item.get("url", "")

            link = "https://www.tutti.ch" + url_item

            if link not in seen:
                seen.add(link)
                results.append((title[:100], link))

        return results

    except:
        return []


# -------------------------
# RICARDO SEARCH
# -------------------------
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


# -------------------------
# SEARCH ALL
# -------------------------
async def search_all():

    results = []
    results += search_tutti()
    results += search_ricardo()

    # сохраняем seen после каждого цикла
    save_seen()

    return results


# -------------------------
# LOOP 15 MIN
# -------------------------
async def loop(app: Application):

    while True:

        if CHAT_ID:

            items = await search_all()

            if items:

                msg = "🚲 Новые велосипеды 0–200 CHF:\n\n"

                for title, link in items:
                    msg += f"{title}\n{link}\n\n"

                await app.bot.send_message(chat_id=CHAT_ID, text=msg)

        await asyncio.sleep(900)


# -------------------------
# STARTUP
# -------------------------
async def post_init(app: Application):
    asyncio.create_task(loop(app))


# -------------------------
# MAIN
# -------------------------
def main():

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))

    print("🚲 Бот запущен...")

    app.run_polling()


if __name__ == "__main__":
    main()
