from flask import Flask
import requests
import threading
import time

# =========================
# CONFIG
# =========================

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"

API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

seen = set()

# =========================
# TELEGRAM SEND
# =========================

def send(text):
    try:
        r = requests.post(
            API_URL + "/sendMessage",
            json={
                "chat_id": CHANNEL_ID,
                "text": text,
                "disable_web_page_preview": False
            },
            timeout=15
        )

        print("SEND:", r.text)

    except Exception as e:
        print("SEND ERROR:", e)

# =========================
# SIMPLE PRICE CHECK
# =========================

def is_good_price(category, price):
    if price is None:
        return False

    if category == "garmin":
        return price <= 50

    if category == "bike":
        return price <= 400

    if category == "macbook":
        return price <= 1200

    return False

# =========================
# FAKE SEARCH PLACEHOLDERS
# (сюда позже подключим реальные источники)
# =========================

def search_ricardo():
    print("RICARDO CHECK")
    return []


def search_tutti():
    print("TUTTI CHECK")
    return []

# =========================
# MONITOR LOOP
# =========================

def monitor():
    print("🟢 MONITOR STARTED")

    send("🟢 Бот запущен\nМониторинг: Garmin + Bikes + MacBook")

    last_alive = 0

    while True:
        try:
            print("🔍 SEARCH START")

            search_ricardo()
            search_tutti()

            # heartbeat
            if time.time() - last_alive > 3600:
                send("💚 Бот работает. Монитор активен.")
                last_alive = time.time()

            print("🔍 SEARCH END")

        except Exception as e:
            print("MONITOR ERROR:", e)

        time.sleep(1800)

# =========================
# FLASK SERVER (Render requirement)
# =========================

@app.route("/")
def home():
    return "bot running"

# =========================
# START
# =========================

if __name__ == "__main__":
    print("🚀 BOT STARTING")

    threading.Thread(target=monitor, daemon=True).start()

    app.run(host="0.0.0.0", port=10000)
