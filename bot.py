from flask import Flask
import threading
import requests
import time
import os
import traceback

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

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
        print("SEND RESPONSE:", r.text)
    except Exception as e:
        print("SEND ERROR:", e)

# ======================
# SAFE TEST REQUEST
# ======================

def test_requests():
    try:
        print("TEST REQUEST START")

        r = requests.get("https://www.ricardo.ch", timeout=10)

        print("RICARDO STATUS:", r.status_code)

        r2 = requests.get("https://www.tutti.ch", timeout=10)

        print("TUTTI STATUS:", r2.status_code)

    except Exception as e:
        print("REQUEST ERROR:")
        traceback.print_exc()

# ======================
# LOOP (FULL DEBUG)
# ======================

def bot_loop():
    print("BOT LOOP STARTED")
    send("🟢 BOT DEBUG v14 STARTED")

    counter = 0

    while True:
        try:
            counter += 1

            print(f"\n===== LOOP {counter} =====")

            test_requests()

            send(f"💚 LOOP OK #{counter}")

        except Exception as e:
            print("LOOP ERROR:")
            traceback.print_exc()

        time.sleep(60)

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

    print("STARTING APP")

    t = threading.Thread(target=bot_loop, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
