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
# SAFE PRICE FILTER
# ======================

def is_good(title, price):
    if price is None:
        return False

    t = title.lower()

    if "garmin" in t and price <= 50:
        return True

    if ("bike" in t or "velo" in t) and price <= 400:
        return True

    if "macbook" in t and price <= 1500:
        return True

    return False

# ======================
# RICARDO SAFE SEARCH
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
                send("🔥 RICARDO DEAL\n" + title + "\n" + str(price) + " CHF\n" + link)

    except Exception as e:
        print("RICARDO ERROR:", e)

# ======================
# TUTTI SAFE SEARCH (NO CRASH)
# ======================

def search_tutti():
    try:
        url = "https://www.tutti.ch/de/li/q/garmin-bike-macbook"

        r = requests.get(url, headers=HEADERS, timeout=20)

        # если блок или ошибка — просто выходим
        if r.status_code != 200:
            print("TUTTI STATUS:", r.status_code)
            return

        html = r.text.lower()

        # простая проверка что сайт жив
        if "tutti" not in html:
            print("TUTTI EMPTY OR BLOCKED")
            return

        if "garmin" in html or "bike" in html:
            print("TUTTI PAGE OK")

    except Exception as e:
        print("TUTTI ERROR:", e)

# ======================
# MONITOR LOOP
# ======================

def monitor():
    print("🚀 BOT STARTED")

    # 🔥 ОБЯЗАТЕЛЬНЫЙ ТЕСТ
    send("🟢 BOT ONLINE TEST\nЕсли ты это видишь — бот работает")

    last_alive = 0

    while True:
        try:
            print("🔍 CYCLE START")

            search_ricardo()
            search_tutti()

            # heartbeat каждые 30 минут
            if time.time() - last_alive > 1800:
                send("💚 Bot alive (monitor running)")
                last_alive = time.time()

            print("🔍 CYCLE END")

        except Exception as e:
            print("MONITOR ERROR:", e)
            send("⚠️ MONITOR ERROR: " + str(e))

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
