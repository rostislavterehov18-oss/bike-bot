from flask import Flask
import requests
import threading
import time

# ======================
# CONFIG
# ======================

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

seen = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ======================
# TELEGRAM SEND
# ======================

def send(text):
    try:
        r = requests.post(
            API_URL + "/sendMessage",
            json={
                "chat_id": CHANNEL_ID,
                "text": text,
                "disable_web_page_preview": True
            },
            timeout=15
        )

        print("SEND RESPONSE:", r.text)

    except Exception as e:
        print("SEND ERROR:", e)

# ======================
# SAFE FILTER (TEMP DEBUG MODE)
# ======================

def is_good(title, price):
    if price is None:
        return False

    t = title.lower()

    # DEBUG MODE (ослаблено чтобы ты видел результаты)
    if "garmin" in t and price <= 200:
        return True

    if ("bike" in t or "velo" in t) and price <= 1000:
        return True

    if "macbook" in t and price <= 3000:
        return True

    return False

# ======================
# RICARDO DEBUG SEARCH
# ======================

def search_ricardo():
    try:
        print("🔎 RICARDO REQUEST...")

        r = requests.get(
            "https://www.ricardo.ch/api/search/v1/search",
            params={"query": "garmin bike velo macbook apple", "limit": 20},
            headers=HEADERS,
            timeout=20
        )

        data = r.json()

        items = data.get("items", [])

        print("RICARDO ITEMS:", len(items))

        for i in items:

            title = (i.get("title") or "").lower()
            price = i.get("price")
            link = i.get("url")

            print("TITLE:", title, "PRICE:", price)

            if not link:
                continue

            if link in seen:
                continue

            seen.add(link)

            if is_good(title, price):
                send("🔥 RICARDO DEAL\n" + title + "\n" + str(price) + " CHF\n" + link)

    except Exception as e:
        print("RICARDO ERROR:", e)

# ======================
# TUTTI DEBUG SEARCH (SAFE)
# ======================

def search_tutti():
    try:
        print("🔎 TUTTI REQUEST...")

        url = "https://www.tutti.ch/de/li/q/garmin-bike-macbook"

        r = requests.get(url, headers=HEADERS, timeout=20)

        print("TUTTI STATUS:", r.status_code)

        if r.status_code != 200:
            return

        html = r.text.lower()

        if "tutti" not in html:
            print("TUTTI BLOCKED OR EMPTY")
            return

        # DEBUG ONLY
        if "garmin" in html:
            print("TUTTI HAS GARMIN DATA")

    except Exception as e:
        print("TUTTI ERROR:", e)

# ======================
# MONITOR LOOP
# ======================

def monitor():
    print("🚀 BOT STARTED")

    send("🟢 BOT START TEST\nЕсли ты это видишь — Telegram работает")

    last_alive = 0

    while True:
        try:
            print("================================")
            print("🔍 CYCLE START")

            search_ricardo()
            search_tutti()

            if time.time() - last_alive > 1800:
                send("💚 Bot alive (debug mode)")
                last_alive = time.time()

            print("🔍 CYCLE END")

        except Exception as e:
            print("MONITOR ERROR:", e)

        time.sleep(1800)

# ======================
# FLASK (RENDER KEEP ALIVE)
# ======================

@app.route("/")
def home():
    return "bot running"

# ======================
# START
# ======================

if __name__ == "__main__":
    print("BOT STARTING")

    threading.Thread(target=monitor, daemon=True).start()

    app.run(host="0.0.0.0", port=10000)
