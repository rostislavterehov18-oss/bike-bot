from flask import Flask
import requests
import threading
import time
import json
import os

# ======================
# CONFIG
# ======================

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

seen = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# ======================
# TELEGRAM
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
        print("SEND:", r.text)

    except Exception as e:
        print("SEND ERROR:", e)

# ======================
# SMART PRICE FILTER
# ======================

def is_good(title, price):
    if price is None:
        return False

    title = title.lower()

    if "garmin" in title and price <= 50:
        return True

    if ("bike" in title or "velo" in title) and price <= 400:
        return True

    if "macbook" in title and price <= 1500:
        return True

    return False

# ======================
# RICARDO (STABLE API)
# ======================

def search_ricardo():
    try:
        r = requests.get(
            "https://www.ricardo.ch/api/search/v1/search",
            params={"query": "garmin bike velo macbook apple", "limit": 20},
            headers=HEADERS,
            timeout=20
        )

        data = r.json()
        items = data.get("items", [])

        for i in items:
            title = (i.get("title") or "").lower()
            price = i.get("price")
            link = i.get("url")

            if not link:
                continue

            if link in seen:
                continue

            seen.add(link)

            if is_good(title, price):
                send(f"🔥 RICARDO DEAL\n{title}\n{price} CHF\n{link}")

    except Exception as e:
        print("RICARDO ERROR:", e)

# ======================
# TUTTI SMART RETRY SYSTEM
# ======================

tutti_fail_count = 0
tutti_cooldown = 0

def search_tutti():
    global tutti_fail_count, tutti_cooldown

    if time.time() < tutti_cooldown:
        print("TUTTI COOLING DOWN...")
        return

    url = "https://www.tutti.ch/de/li/q/garmin-bike-macbook"

    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)

            # BLOCKED OR ERROR
            if r.status_code in [403, 429, 503]:
                print(f"TUTTI BLOCKED {r.status_code}")
                raise Exception("blocked")

            html = r.text.lower()

            if "garmin" in html or "bike" in html:
                print("TUTTI OK")

            else:
                print("TUTTI EMPTY RESPONSE")

            tutti_fail_count = 0
            return html

        except Exception as e:
            print(f"TUTTI FAIL attempt {attempt+1}", e)
            time.sleep(5 * (attempt + 1))

    # ======================
    # FAILURE MODE
    # ======================

    tutti_fail_count += 1
    print("TUTTI DOWN COUNT:", tutti_fail_count)

    # cooldown system
    if tutti_fail_count >= 3:
        tutti_cooldown = time.time() + 600  # 10 min pause
        send("⚠️ Tutti временно недоступен, переключаюсь на Ricardo")

    return None

# ======================
# MONITOR LOOP
# ======================

def monitor():
    print("🚀 BOT V5 STARTED")

    send("🟢 Bot V5 started\nSmart monitoring active")

    last_alive = 0

    while True:
        try:
            print("🔍 SEARCH CYCLE START")

            search_ricardo()
            search_tutti()

            # heartbeat
            if time.time() - last_alive > 3600:
                send("💚 Bot alive (V5 Smart Mode)")
                last_alive = time.time()

            print("🔍 SEARCH CYCLE END")

        except Exception as e:
            print("MONITOR ERROR:", e)

        time.sleep(1800)

# ======================
# FLASK (RENDER)
# ======================

@app.route("/")
def home():
    return "Bot V5 running"

# ======================
# START
# ======================

if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
