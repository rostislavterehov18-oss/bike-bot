from flask import Flask, request
import requests

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)


# ----------------------------
# ПОИСК GARMIN
# ----------------------------
def find_item():
    url = "https://www.ricardo.ch/api/search/v1/search"

    params = {
        "query": "Garmin GPS navigator",
        "priceTo": 50,
        "limit": 1
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)

        # защита от пустого ответа
        if not r.text:
            return "❌ пустой ответ от API"

        # защита от HTML вместо JSON
        if "json" not in r.headers.get("Content-Type", ""):
            return "❌ API вернул не JSON"

        data = r.json()

        items = data.get("items", [])
        if not items:
            return "❌ ничего не найдено до 50 CHF"

        item = items[0]

        title = item.get("title", "no title")
        link = item.get("url", "")

        if not link.startswith("http"):
            link = "https://www.ricardo.ch" + link

        return f"🛰 Garmin GPS\n{title}\n{link}"

    except Exception as e:
        return f"❌ ошибка API: {str(e)}"


# ----------------------------
# ОТПРАВКА СООБЩЕНИЯ
# ----------------------------
def send_message(chat_id, text):
    requests.post(API_URL + "/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })


# ----------------------------
# ПРОВЕРКА СЕРВЕРА
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "Bot is alive"


# ----------------------------
# WEBHOOK
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
# ЗАПУСК СЕРВЕРА
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
