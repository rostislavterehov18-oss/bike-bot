from flask import Flask, request
import requests

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)


# ----------------------------
# ПОИСК ТОВАРА (RICARDO)
# ----------------------------
def find_item():
    url = "https://www.ricardo.ch/api/search/v1/search"

    params = {
        "query": "Garmin GPS navigator",
        "priceTo": 50,
        "limit": 1
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()

        items = data.get("items", [])
        if not items:
            return "❌ Нет Garmin до 50 CHF"

        item = items[0]

        title = item.get("title", "no title")
        link = item.get("url", "")

        if not link.startswith("http"):
            link = "https://www.ricardo.ch" + link

        return f"🛰 Garmin GPS\n{title}\n{link}"

    except Exception as e:
        return f"❌ ошибка поиска: {str(e)}"


# ----------------------------
# ОТПРАВКА СООБЩЕНИЯ
# ----------------------------
def send_message(chat_id, text):
    requests.post(API_URL + "/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })


# ----------------------------
# ПРИВЕТСТВИЕ СЕРВЕР
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "Bot is alive"


# ----------------------------
# WEBHOOK TELEGRAM
# ----------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if not data:
        return "ok"

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_message(chat_id, "🛰 Бот запущен\nПоиск: Garmin GPS до 50 CHF")

        elif text == "/check":
            send_message(chat_id, find_item())

    return "ok"


# ----------------------------
# START SERVER
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
