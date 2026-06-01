from flask import Flask, request
import requests

TOKEN = "8793663575:AAGbaqYzho2l3_MTceRW33SEvd_yEj2h8BU"
URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

# -------------------
def find_bike():
    url = "https://www.tutti.ch/api/v10/search"

    params = {
        "query": "velo bike fahrrad",
        "priceTo": 200,
        "limit": 1
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        for item in data.get("items", []):
            title = item.get("title", "no title")
            link = "https://www.tutti.ch" + item.get("url", "")
            return f"🚲 {title}\n{link}"

        return "❌ нет товаров"
    except:
        return "❌ ошибка"


# -------------------
@app.route("/", methods=["GET"])
def home():
    return "Bot is alive"


# -------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_message(chat_id, "🚲 бот работает")

        elif text == "/check":
            send_message(chat_id, find_bike())

    return "ok"


# -------------------
def send_message(chat_id, text):
    requests.post(
        URL + "/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )


# -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
