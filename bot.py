from flask import Flask
import threading
import requests
import time
import os

# ======================
# CONFIG
# ======================

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

seen = set()

# ======================
# TELEGRAM
# ======================

def send(text):
    try:
        requests.post(
            API_URL + "/sendMessage",
            json={
                "chat_id": CHANNEL_ID,
                "text": text,
                "disable_web_page_preview": True
            },
            timeout=10
        )
        print("SEND:", text)

    except Exception as e:
        print("SEND ERROR:", e)

# ======================
# SAFE RICARDO CHECK
# ======================

def ricardo_check():
    try:
        print("RICARDO CHECK...")

        r = requests.get(
            "https://www.ricardo.ch/de/c/all?query=bike",
            headers=HEADERS,
            timeout=15
        )

        if r.status_code != 200:
            print("RICARDO STATUS:", r.status_code)
            return

        if "html" not in r.text.lower():
            print("RICARDO EMPTY RESPONSE")
            return

        send("📡 Ricardo scan OK")

    except Exception as e:
        print("RICARDO ERROR:", e)

# ======================
# SAFE TUTTI CHECK
# ======================

def tutti_check():
    try:
        print("TUTTI CHECK...")

        r = requests.get(
            "https://www.tutti.ch/de/li/q/bike",
            headers=HEADERS,
            timeout=15
        )

        print("TUTTI STATUS:", r.status_code)

        if r.status_code == 403:
            print("TUTTI BLOCKED")
            return

        send("📡 Tutti scan OK")

    except Exception as e:
        print("TUTTI ERROR:", e)

# ======================
# BOT LOOP (WORKER)
# ======================

def bot_loop():
    print("BOT LOOP STARTED")

    send("🟢 BOT ONLINE v12")

    counter = 0

    while True:
        try:
            counter += 1

            print("LOOP:", counter)

            ricardo_check()
            tutti_check()

            # heartbeat
            if counter % 10 == 0:
                send("💚 Bot alive heartbeat")

        except Exception as e:
            print("LOOP ERROR:", e)

        time.sleep(60)

# ======================
# FLASK ROUTES (REQUIRED FOR RENDER)
# ======================

@app.route("/")
def home():
    return "bot alive"

@app.route("/health")
def health():
    return "ok"

# ======================
# START
# ======================

if __name__ == "__main__":

    print("STARTING APP")

    # start bot in background
    thread = threading.Thread(target=bot_loop)
    thread.daemon = True
    thread.start()

    # IMPORTANT: keep port open for Render
    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)
