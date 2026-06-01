from flask import Flask
import requests
import threading
import time
import os

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0"}

started = False

# ======================
# TELEGRAM
# ======================

def send(text):
    try:
        requests.post(
            API_URL + "/sendMessage",
            json={"chat_id": CHANNEL_ID, "text": text},
            timeout=10
        )
        print("SEND OK:", text)
    except Exception as e:
        print("SEND ERROR:", e)

# ======================
# BOT LOOP
# ======================

def bot_loop():
    print("BOT LOOP STARTED")

    send("🟢 BOT ONLINE (Render FIX v10)")

    while True:
        try:
            print("LOOP RUNNING")

            # минимальный тест чтобы не падал
            r = requests.get(
                "https://www.ricardo.ch",
                timeout=10
            )

            print("RICARDO STATUS:", r.status_code)

        except Exception as e:
            print("LOOP ERROR:", e)

        time.sleep(60)

# ======================
# FLASK ROUTE
# ======================

@app.route("/")
def home():
    global started

    # 🔥 стартуем бот ТОЛЬКО когда Render уже открыл порт
    if not started:
        started = True
        threading.Thread(target=bot_loop, daemon=True).start()
        print("BOT THREAD STARTED")

    return "bot alive"

# ======================
# START SERVER
# ======================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    print("STARTING FLASK ON PORT", port)

    # ⚠️ ВАЖНО: Flask СРАЗУ стартует
    app.run(host="0.0.0.0", port=port)
