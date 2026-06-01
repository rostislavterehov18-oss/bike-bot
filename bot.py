from flask import Flask, request
import requests
import threading
import time

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

CHAT_ID = None
seen = set()


# ----------------------------
# TELEGRAM SEND
# ----------------------------
def send_message(chat_id, text):
    try:
        requests.post(
            API_URL + "/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10
        )
    except:
        pass


# ----------------------------
# SEARCH GARMIN (SAFE)
# ----------------------------
def search_items():
    url = "https://www.ricardo.ch/de/c/gps-navigation/"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)

        if not r.text:
            return []

        results = []

        parts = r.text.split('href="')

        for part in parts:
            if "/de/a/" in part:
                link = part.split('"')[0]

                if not link.startswith("http"):
                    link = "https://www.ricardo.ch" + link

                if link in seen:
                    continue

                seen.add(link)

                results.append(f"🛰 Garmin / GPS\n{link}")

                if len(results) >= 3:
                    break

        return results

    except:
        return []


# ----------------------------
# MONITOR LOOP
# ----------------------------
def monitor():
    while True:
        try:
            if CHAT_ID:
                items = search_items()

                for item in items:
                    send_message(CHAT_ID, item)

            time.sleep(600)  # 10 min

        except:
            time.sleep(60)


# ----------------------------
# WEBHOOK ROUTE
# ----------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    global CHAT_ID

    data = request.get_json()

    if not data:
        return "ok"

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        CHAT_ID = chat_id

        if text == "/start":
            send_message(chat_id, "🛰 Бот запущен\nПоиск: Garmin GPS до 50 CHF")

        elif text == "/check":
            items = search_items()
            if items:
                send_message(chat_id, "\n\n".join(items))
            else:
                send_message(chat_id, "❌ ничего не найдено")

    return "ok"


# ----------------------------
# HOME ROUTE
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "Bot is running"


# ----------------------------
# START
# ----------------------------
if __name__ == "__main__":
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()

    app.run(host="0.0.0.0", port=10000)
