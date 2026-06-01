from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os

TOKEN = "8793663575:AAGbaqYzho2l3_MTceRW33SEvd_yEj2h8BU"

PORT = int(os.environ.get("PORT", 10000))

# ⚠️ ВАЖНО: поменяй на свой Render URL
WEBHOOK_URL = "https://bike-bot-1.onrender.com"


# -----------------------
def find_bike():
    url = "https://www.tutti.ch/api/v10/search"

    params = {
        "query": "velo bike fahrrad",
        "priceTo": 200,
        "limit": 5
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        for item in data.get("items", []):
            title = item.get("title", "no title")
            link = "https://www.tutti.ch" + item.get("url", "")
            return f"🚲 {title}\n{link}"

        return "❌ Нет товаров"

    except:
        return "❌ Ошибка API"


# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚲 Бот работает!\n\n"
        "/check - проверить велосипеды"
    )


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(find_bike())


# -----------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))

    print("BOT STARTED")

    # 🔥 WEBHOOK режим (главное отличие!)
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
