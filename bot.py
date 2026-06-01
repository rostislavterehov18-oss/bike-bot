from flask import Flask
import requests
import threading
import time
import sys

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ======================
# TELEGRAM (SAFE)
# ======================

def send(text):
    try:
        r = requests.post(
            API_URL + "/sendMessage",
            json={"chat_id": CHANNEL_ID, "text": text},
            timeout=10
        )
        print("SEND:", r.text)
    except Exception as e:
        print("SEND ERROR:", e)

# ======================
# DEBUG RICARDO
# ======================

def search_ricardo():
    print("🔎 RICARDO RUNNING")

    try:
        r = requests.get(
            "https://www.ricardo.ch/api/search/v1/search",
            params={"query": "garmin bike velo macbook", "limit": 10},
            headers=HEADERS,
            timeout=15
        )

        data = r.json()
        items = data.get("items", [])

        print("RICARDO ITEMS:", len(items))

        for i in items[:5]:
            print("ITEM:", i.get("title"), i.get("price"))

    except Exception as e:
        print("RICARDO ERROR:", e)

# ======================
# DEBUG TUTTI
# ======================

def search_tutti():
    print("🔎 TUTTI RUNNING")

    try:
        r = requests.get(
            "https://www.tutti.ch/de/li/q/bike",
            headers=HEADERS,
            timeout=15
        )

        print("TUTTI STATUS:", r.status_code)

    except Exception as e:
        print("TUTTI ERROR:", e)

# ======================
# MONITOR (FORCED LOOP)
# ======================

def monitor():
    print("🚀 MONITOR THREAD STARTED")
    sys.stdout.flush()

    counter = 0

    while True:
        try:
            counter += 1

            print(f"🔁 LOOP {counter}")

            search_ricardo()
            search_tutti()

            if counter == 1:
                send("🟢 BOT START CONFIRMED")

        except Exception as e:
            print("MONITOR CRASH:", e)

        time.sleep(30)

# ======================
# FLASK
# ======================

@app.route("/")
def home():
    return "alive"

# ======================
# START (IMPORTANT FIX)
# ======================

if __name__ == "__main__":
    print("BOT STARTING")

    # 🔥 CRITICAL: start thread BEFORE flask blocks
    t = threading.Thread(target=monitor)
    t.daemon = True
    t.start()

    # small delay to ensure thread starts
    time.sleep(2)

    send("🟢 MANUAL START TEST")

    app.run(host="0.0.0.0", port=10000)
