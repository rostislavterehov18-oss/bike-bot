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
        requests.post(API_URL + "/sendMessage", json={
            "chat_id": chat_id,
            "text": text
        }, timeout=10)
    except:
        pass


# ----------------------------
# STABLE SEARCH (HTML BASED)
# ----------------------------
def search_items():
    url = "https://www.ricardo.ch/de/c/gps-navigation/"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)

        if not r.text or len(r.text) < 3000:
            return []

        html = r.text
        results = []

        # ищем ссылки на товары
        parts = html.split('href="')

        for part in parts:
            if "/de/a/" in part:
                link = part.split('"')[0]

                if not link.startswith("http"):
                    link = "https://www.ricardo.ch" + link

                if link in seen:
                    continue

                seen.add(link)

                results.append("🛰 Garmin / GPS найден\n" + link)

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

            time.sleep(600)  # 10 минут

        except:
            time.sleep(60)


# ----------------------------
# WEBHOOK
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
            send_message(chat_id, "🛰 Монитор запущен\nGarmin GPS поиск активен")

        elif text == "/check":
            items = search_items()

            if items:
                send_message(chat_id, "\n\n".join(items))
            else:
                send_message(chat_id, "❌ новых объявлений нет")

    return "ok"


# ----------------------------
# START SERVER
# ----------------------------
if __name__ == "__main__":
    t = threading.Thread(target=monitor, daemon=True)
    t.start()

    app.run(host="0.0.0.0", port=10000)
