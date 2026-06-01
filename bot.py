from flask import Flask, request
import requests
import threading
import time
import json
import os

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
API_URL = f"https://api.telegram.org/bot{TOKEN}"
CHANNEL_ID = "@swiss_bike"

app = Flask(__name__)

seen = set()
DB_FILE = "price_db.json"


# ----------------------------
# 📦 загрузка базы цен
# ----------------------------
def load_db():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db[-2000:], f)  # ограничение размера


price_db = load_db()


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
# 🧠 ОБУЧЕНИЕ РЫНКА (простая статистика)
# ----------------------------
def update_market(title, p):
    global price_db

    if p is None:
        return

    price_db.append({
        "title": title.lower(),
        "price": p,
        "time": time.time()
    })

    save_db(price_db)


# ----------------------------
def get_market_price(title):
    t = title.lower()

    matches = [
        x["price"] for x in price_db
        if any(w in x["title"] for w in t.split())
    ]

    if len(matches) < 3:
        return None  # недостаточно данных

    return sum(matches) / len(matches)


# ----------------------------
def score(title, price_val):
    market = get_market_price(title)

    if market is None:
        # fallback
        market = price_val * 1.3 if price_val else 500

    if price_val is None:
        return 40

    ratio = price_val / market

    if ratio < 0.5:
        return 95
    if ratio < 0.7:
        return 80
    if ratio < 0.9:
        return 65
    return 40


# ----------------------------
def is_good(title, price_val):
    return score(title, price_val) >= 75


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

        for i in items:
            title = (i.get("title") or "").lower()
            link = i.get("url") or ""
            p = price(i.get("price"))

            if not link.startswith("http"):
                link = "https://www.ricardo.ch" + link

            if link in seen:
                continue

            update_market(title, p)

            # 🛰 GARMIN
            if "garmin" in title and p and p <= 50:
                seen.add(link)
                send(f"🛰 GARMIN\n{title}\n{p} CHF\n🔥 score {score(title,p)}\n{link}")

            # 🚲 BIKE
            elif any(x in title for x in ["bike", "velo"]) and p and p <= 400:
                if is_good(title, p):
                    seen.add(link)
                    send(f"🚲 BIKE\n{title}\n{p} CHF\n🔥 score {score(title,p)}\n{link}")

            # 💻 MACBOOK (2019+ логика)
            elif "macbook" in title and p and p <= 2500:
                if is_good(title, p):
                    seen.add(link)
                    send(f"💻 APPLE\n{title}\n{p} CHF\n🔥 score {score(title,p)}\n{link}")

        return []

    except Exception as e:
        print("RICARDO ERROR:", e)
        return []


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

        for i in items:
            title = (i.get("title") or "").lower()
            link = i.get("url") or ""
            p = price(i.get("price"))

            if not link.startswith("http"):
                link = "https://www.tutti.ch" + link

            if link in seen:
                continue

            update_market(title, p)

            if "garmin" in title and p and p <= 50:
                seen.add(link)
                send(f"🛰 GARMIN\n{title}\n{p} CHF\n🔥 score {score(title,p)}\n{link}")

            elif any(x in title for x in ["bike", "velo"]) and p and p <= 400:
                if is_good(title, p):
                    seen.add(link)
                    send(f"🚲 BIKE\n{title}\n{p} CHF\n🔥 score {score(title,p)}\n{link}")

            elif "macbook" in title:
                if is_good(title, p):
                    seen.add(link)
                    send(f"💻 MACBOOK\n{title}\n{p} CHF\n🔥 score {score(title,p)}\n{link}")

        return []

    except Exception as e:
        print("TUTTI ERROR:", e)
        return []


# ----------------------------
def monitor():
    while True:
        search_ricardo()
        search_tutti()
        time.sleep(1800)


# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "AI price tracker running"


# ----------------------------
if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
