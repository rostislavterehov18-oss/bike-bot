from flask import Flask, request
import requests

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)


# -----------------------
def find_item():
    url = "https://www.ricardo.ch/api/search/v1/search"

    params = {
        "query": "Garmin GPS",
        "priceTo": 50,
        "limit": 5
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()

        items = data.get("items", [])
        if not items:
            return "❌ ничего не найдено"

        item = items[0]

        title = item.get("title", "no title")
        link = item.get("url", "")

        if not link.startswith("http"):
            link = "https://www.ricardo.ch" + link

        return f"🛰 Garmin GPS (Ricardo)\n{title}\n{link}"

    except Exception as e:
        return f"❌ ошибка: {str(e)}"def find_item():
    url = "https://www.ricardo.ch/api/search/v1/search"

    params = {
        "query": "Garmin GPS",
        "priceTo": 50,
        "limit": 5
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()

        items = data.get("items", [])
        if not items:
            return "❌ ничего не найдено"

        item = items[0]

        title = item.get("title", "no title")
        link = item.get("url", "")

        if not link.startswith("http"):
            link = "https://www.ricardo.ch" + link

        return f"🛰 Garmin GPS (Ricardo)\n{title}\n{link}"

    except Exception as e:
        return f"❌ ошибка: {str(e)}"

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
