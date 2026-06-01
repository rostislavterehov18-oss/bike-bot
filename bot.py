from flask import Flask, request
import requests

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)


def send_message(chat_id, text):
    requests.post(URL + "/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })


def find_bike():
    r = requests.get("https://www.tutti.ch/api/v10/search", params={
        "query": "velo bike fahrrad",
        "priceTo": 200,
        "limit": 1
    })

    data = r.json()

    for item in data.get("items", []):
        title = item.get("title", "no title")
        link = "https://www.tutti.ch" + item.get("url", "")
        return f"🚲 {title}\n{link}"

    return "❌ нет товаров"


@app.route("/", methods=["GET"])
def home():
    return "OK"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_message(chat_id, "🚲 бот работает")

        if text == "/check":
            send_message(chat_id, find_bike())

    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
