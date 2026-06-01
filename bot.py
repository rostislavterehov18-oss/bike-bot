from flask import Flask
import requests
import threading
import time
import re
import os

# ======================
# CONFIG
# ======================

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0"}

seen = set()

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
        print("SEND OK")
    except Exception as e:
        print("SEND ERROR:", e)

# ======================
# SIMPLE FILTER
# ======================

def is_good(title, price):
    if price is None:
        return False

    t = title.lower()

    if "garmin" in t and price <= 50:
        return True

    if ("bike" in t or "velo" in t) and price <= 400:
        return True

    return False

# ======================
# RICARDO SAFE
# ======================

def search_ricardo():
    try:
        print("RICARDO RUN")

        r = requests.get(
            "https://www.ricardo.ch/de/c/all?query=bike",
            headers=HEADERS,
            timeout=20
        )

        if r.status_code != 200:
            print("RICARDO STATUS:", r.status_code)
            return

        links = re.findall(r'href="(/de/a/[^"]+)"', r.text)

        print("RICARDO LINKS:", len(links))

        for l in links[:10]:
            full = "https://www.ricardo.ch" + l

            if full in seen:
                continue

            seen.add(full)

            send("📦 Ricardo found:\n" + full)

    except Exception as e:
        print("RICARDO ERROR:", e)

# ======================
# TUTTI SAFE
# ======================

def search_tutti():
    try:
        print("TUTTI RUN")

        r = requests.get(
            "https://www.tutti.ch/de/li/q/bike",
            headers=HEADERS,
            timeout=20
        )

        print("TUTTI STATUS:", r.status_code)

    except Exception as e:
        print("TUTTI ERROR:", e)

# ======================
# MONITOR LOOP (THREAD SAFE)
# ======================

def monitor():
    print("MONITOR STARTED")

    send("🟢 BOT STARTED SUCCESSFULLY")

    while True:
        try:
            search_ricardo()
            search_tutti()

        except Exception as e:
            print("LOOP ERROR:", e)

        time.sleep(60)

# ======================
# FLASK ROUTE (IMPORTANT)
# ======================

@app.route("/")
def home():
    return "bot alive"

# ======================
# STARTUP (IMPORTANT FIX)
# ======================

if __name__ == "__main__":
    print("MAIN START")

    # 🔥 start background thread FIRST
    t = threading.Thread(target=monitor)
    t.daemon = True
    t.start()

    # 🔥 THEN start web server (Render needs this)
    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)
