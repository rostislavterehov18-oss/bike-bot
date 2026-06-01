from flask import Flask, request
import requests
import threading
import time

TOKEN = "В8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

CHANNEL_ID = "@swiss_bike"

app = Flask(__name__)

seen = set()


# ----------------------------
def send(text):
    try:
        requests.post(API_URL + "/sendMessage", json={
            "chat_id": CHANNEL_ID,
            "text": text,
            "disable_web_page_preview": False
        }, timeout=10)
    except:
        pass


HEADERS = {"User-Agent": "Mozilla/5.0"}


# ----------------------------
def price(p):
    try:
        return float(p)
    except:
        return None


# ----------------------------
# 🧠 РЫНОЧНАЯ ОЦЕНКА (упрощённая)
# ----------------------------
def market_value(title):
    t = title.lower()

    if "macbook pro" in t:
        return 1200
    if "macbook air" in t:
        return 900
    if "garmin" in t:
        return 120
    if any(x in t for x in ["bike", "velo", "fahrrad"]):
        return 600

    return 300


# ----------------------------
def score(title, price_val):
    if price_val is None:
        return 40

    market = market_value(title)

    ratio = price_val / market

    if ratio < 0.4:
        return 95
    if ratio < 0.6:
        return 80
    if ratio < 0.8:
        return 65
    return 40


# ----------------------------
def is_good(title, price_val):
    s = score(title, price_val)
    return s >= 75


# ----------------------------
# 🛰 RICARDO
# ----------------------------
def search_ricardo():
    try:
        r = requests.get(
            "https://www.ricardo.ch/api/search/v1/search",
            params={"query": "garmin bike velo macbook apple laptop", "limit": 30},
            headers=HEADERS,
            timeout=20
        )

        data = r.json()
        items = data.get("items", [])

        results = []

        for i in items:
            title = (i.get("title") or "").lower()
            link = i.get("url") or ""
            p = price(i.get("price"))

            if not link.startswith("http"):
                link = "https://www.ricardo.ch" + link

            if link in seen:
                continue

            # 🛰 GARMIN
            if "garmin" in title and p and p <= 50:
                seen.add(link)
                send(f"🛰 GARMIN\n{title}\n{p} CHF\n{link}")
                continue

            # 🚲 BIKE
            if any(x in title for x in ["bike", "velo", "fahrrad"]) and p and p <= 400:
                if is_good(title, p):
                    seen.add(link)
                    send(f"🚲 BIKE DEAL\n{title}\n{p} CHF (🔥 {score(title,p)}/100)\n{link}")
                continue

            # 💻 MACBOOK
            if "macbook" in title and p and p <= 2000:
                if is_good(title, p):
                    seen.add(link)
                    send(f"💻 APPLE DEAL\n{title}\n{p} CHF (🔥 {score(title,p)}/100)\n{link}")
                continue

        return []

    except:
        return []


# ----------------------------
# 🟡 TUTTI
# ----------------------------
def search_tutti():
    try:
        r = requests.get(
            "https://www.tutti.ch/api/v10/search",
            params={"query": "garmin bike macbook apple laptop velo", "limit": 30},
            headers=HEADERS,
            timeout=20
        )

        if "json" not in r.headers.get("Content-Type", ""):
            return []

        data = r.json()
        items = data.get("items", [])

        results = []

        for i in items:
            title = (i.get("title") or "").lower()
            link = i.get("url") or ""
            p = price(i.get("price"))

            if not link.startswith("http"):
                link = "https://www.tutti.ch" + link

            if link in seen:
                continue

            if "garmin" in title and p and p <= 50:
                seen.add(link)
                send(f"🛰 GARMIN\n{title}\n{p} CHF\n{link}")

            elif any(x in title for x in ["bike", "velo"]) and p and p <= 400:
                if is_good(title, p):
                    seen.add(link)
                    send(f"🚲 BIKE\n{title}\n{p} CHF\n{link}")

            elif "macbook" in title and p:
                if is_good(title, p):
                    seen.add(link)
                    send(f"💻 APPLE MACBOOK\n{title}\n{p} CHF\n{link}")

        return []

    except:
        return []


# ----------------------------
# 📘 FACEBOOK (ОПЦИОНАЛЬНО)
# ----------------------------
def search_facebook():
    # ⚠️ реальный парсинг нестабилен
    return []


# ----------------------------
def monitor():
    while True:
        search_ricardo()
        search_tutti()
        search_facebook()
        time.sleep(1800)  # 30 минут


# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "ultimate monitor running"


# ----------------------------
if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
