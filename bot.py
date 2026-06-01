from flask import Flask
import requests
import time
import re

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
        print("SEND OK:", text)
    except Exception as e:
        print("SEND ERROR:", e)

# ======================
# FILTER
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
# SIMPLE RICARDO (SAFE)
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

            send("📦 Ricardo item found:\n" + full)

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
# MAIN LOOP (NO THREAD)
# ======================

def run_bot():
    print("BOT STARTED")

    send("🟢 BOT ONLINE (v9 safe loop)")

    while True:
        try:
            search_ricardo()
            search_tutti()

        except Exception as e:
            print("LOOP ERROR:", e)

        time.sleep(60)

# ======================
# FLASK
# ======================

@app.route("/")
def home():
    return "alive"

# ======================
# START
# ======================

if __name__ == "__main__":
    run_bot()
    app.run(host="0.0.0.0", port=10000)
