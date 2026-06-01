from flask import Flask
import threading
import requests
import time
import os
import traceback
import sys

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

# ======================
# PRINT FORCE FLUSH (ВАЖНО ДЛЯ RENDER)
# ======================

def log(msg):
    print(msg)
    sys.stdout.flush()

# ======================
# TELEGRAM
# ======================

def send(text):
    try:
        r = requests.post(
            API_URL + "/sendMessage",
            json={"chat_id": CHANNEL_ID, "text": text},
            timeout=10
        )
        log("SEND OK: " + r.text)
    except Exception as e:
        log("SEND ERROR")
        traceback.print_exc()

# ======================
# SAFE REQUEST WRAPPER
# ======================

def safe_get(url):
    log(f"REQUEST -> {url}")
    try:
        r = requests.get(url, timeout=10)
        log(f"STATUS {url} -> {r.status_code}")
        return r.status_code
    except Exception:
        log("REQUEST FAILED")
        traceback.print_exc()
        return None

# ======================
# LOOP
# ======================

def bot_loop():
    log("🚀 BOT LOOP STARTED (V15)")

    send("🟢 BOT V15 STARTED")

    counter = 0

    while True:
        try:
            counter += 1
            log(f"\n===== LOOP {counter} =====")

            log("STEP 1: RICARDO")
            safe_get("https://www.ricardo.ch")

            log("STEP 2: TUTTI")
            safe_get("https://www.tutti.ch")

            send(f"💚 LOOP OK {counter}")

        except Exception:
            log("LOOP CRASHED")
            traceback.print_exc()

        time.sleep(30)

# ======================
# FLASK
# ======================

@app.route("/")
def home():
    return "bot alive"

# ======================
# START
# ======================

if __name__ == "__main__":

    log("STARTING APP")

    t = threading.Thread(target=bot_loop, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)
