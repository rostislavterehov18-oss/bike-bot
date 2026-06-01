from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import json
import os

TOKEN = "8793663575:AAGbaqYzho2l3_MTceRW33SEvd_yEj2h8BU"

seen_file = "seen.json"

# --------------------
# LOAD SEEN
# --------------------
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


# --------------------
# SEARCH (1 ITEM ONLY)
# --------------------
def find_bike():
    url = "https://www.tutti.ch/api/v10/search"

    params = {
        "query": "velo bike fahrrad",
        "priceTo": 200,
        "limit": 10
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        for item in data.get("items", []):
            title = item.get("title", "no title")
            link = "https://www.tutti.ch" + item.get("url", "")

            if link not in seen:
                seen.add(link)
                save_seen()
                return f"🚲 {title}\n{link}"

        return "❌ Новых велосипедов нет"

    except:
        return "❌ Ошибка запроса"


# --------------------
# COMMANDS
# --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚲 Бот запущен\n\n"
        "/check - проверить велосипеды"
    )


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = find_bike()
    await update.message.reply_text(result)


# --------------------
# MAIN
# --------------------
def main():
    # ⚠️ ОДИН И ЕДИНСТВЕННЫЙ app
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))

    print("BOT STARTED")

    # 🔥 ВАЖНО: защита от лишних обновлений
    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
