from flask import Flask, request
import requests

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)


# -----------------------
def find_item():
    url = "https://www.tutti.ch/api/v10/search"

    params = {
        "query": "Garmin GPS navigator navigation",
        "priceTo": 50,
        "limit": 1
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        for item in data.get("items", []):
            title = item.get("title", "no title")
            link = "https://www.tutti.ch" + item.get("url", "")
            return f"🛰 Garmin GPS\n{title}\n{link}"

        return "❌ Нет товаров до 50 CHF"

    except:
        return "❌ Ошибка поиска"


# -----------------------
def send_message(chat_id, text):
    requests.post(URL + "/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })


# -----------------------
@app.route("/", methods=["GET"])
def home():
    return "Bot is alive"


# -----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_message(chat_id, "🛰 Бот запущен (Garmin поиск до 50 CHF)")

        elif text == "/check":
            send_message(chat_id, find_item())

    return "ok"


# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
