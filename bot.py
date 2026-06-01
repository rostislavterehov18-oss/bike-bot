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
def send_message(chat_id, text):
    try:
        requests.post(API_URL + "/sendMessage", json={
            "chat_id": chat_id,
            "text": text
        }, timeout=10)
    except:
        pass


# ----------------------------
# 🔵 SOURCE 1: RICARDO (ВСЯ ШВЕЙЦАРИЯ)
# ----------------------------
def search_ricardo():
    url = "https://www.ricardo.ch/de/c/navigationssysteme/"

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if not r.text:
            return []

        results = []
        parts = r.text.split('href="')

        for p in parts:
            if "/de/a/" in p:
                link = p.split('"')[0]

                if not link.startswith("http"):
                    link = "https://www.ricardo.ch" + link

                if link in seen:
                    continue

                seen.add(link)
                results.append("🛰 Ricardo GPS\n" + link)

                if len(results) >= 3:
                    break

        return results

    except:
        return []


# ----------------------------
# 🟠 SOURCE 2: TUTTI (ВСЯ ШВЕЙЦАРИЯ)
# ----------------------------
def search_tutti():
    url = "https://www.tutti.ch/de/li/ganze-schweiz/fahrzeuge/navigationssysteme"

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if not r.text:
            return []

        results = []
        parts = r.text.split('href="')

        for p in parts:
            if "/de/vi/" in p:
                link = p.split('"')[0]

                if not link.startswith("http"):
                    link = "https://www.tutti.ch" + link

                if link in seen:
                    continue

                seen.add(link)
                results.append("🛰 Tutti GPS\n" + link)

                if len(results) >= 3:
                    break

        return results

    except:
        return []


# ----------------------------
# 🔁 ОБЩИЙ ПОИСК
# ----------------------------
def search_all():
    results = []

    results += search_ricardo()
    results += search_tutti()

    return results


# ----------------------------
# MONITOR
# ----------------------------
def monitor():
    while True:
        try:
            if CHAT_ID:
                items = search_all()

                for i in items:
                    send_message(CHAT_ID, i)

            time.sleep(600)

        except:
            time.sleep(60)


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
            send_message(chat_id, "🛰 Монитор Швейцарии запущен\nRicardo + Tutti")

        elif text == "/check":
            items = search_all()

            if items:
                send_message(chat_id, "\n\n".join(items))
            else:
                send_message(chat_id, "❌ ничего не найдено по Швейцарии")

    return "ok"


# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "Swiss bot running"


# ----------------------------
if __name__ == "__main__":
    t = threading.Thread(target=monitor, daemon=True)
    t.start()

    app.run(host="0.0.0.0", port=10000)
