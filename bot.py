from flask import Flask
import requests
import threading
import time
import json
import os

# =========================
# CONFIG
# =========================

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

seen = set()

DB_FILE = "price_db.json"
daily_deals = []

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =========================
# LOAD PRICE DB
# =========================

def load_db():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []

price_db = load_db()

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(price_db[-3000:], f)

# =========================
# TELEGRAM
# =========================

def send(text):
    try:
        r = requests.post(API_URL + "/sendMessage", json={
            "chat_id": CHANNEL_ID,
            "text": text,
            "disable_web_page_preview": True
        }, timeout=15)

        print("SEND:", r.text)

    except Exception as e:
        print("SEND ERROR:", e)

# =========================
# SMART PRICE MODEL (AI-LIKE)
# =========================

def market_price(keyword):
    prices = [
        x["price"] for x in price_db
        if keyword in x["title"]
    ]

    if len(prices) < 5:
        return None

    prices.sort()
    return prices[len(prices)//2]  # median

def deal_score(price, market):
    if not market:
        return 50

    ratio = price / market

    if ratio < 0.5:
        return 95
    if ratio < 0.7:
        return 80
    if ratio < 0.9:
        return 65
    return 40

# =========================
# FILTERS
# =========================

def is_free_or_broken(text):
    t = text.lower()

    free_words = [
        "gratis", "free", "kostenlos",
        "zu verschenken", "giveaway", "for free"
    ]

    broken_words = [
        "defekt", "kaputt", "not working",
        "for parts", "broken", "repair"
    ]

    return any(w in t for w in free_words + broken_words)

# =========================
# SAVE MARKET DATA
# =========================

def update_db(title, price):
    if price is None:
        return

    price_db.append({
        "title": title,
        "price": price,
        "time": time.time()
    })

    save_db()

# =========================
# DEAL TRACKER
# =========================

def add_deal(item):
    daily_deals.append(item)

# =========================
# RICARDO (SIMPLIFIED)
# =========================

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

            if not link or link in seen:
                continue

            seen.add(link)

            update_db(title, price)

            market = market_price("bike" if "bike" in title else "garmin")
            score = deal_score(price or 999, market)

            text = f"{title}\n{price} CHF\nscore: {score}\n{link}"

            # FREE / BROKEN
            if is_free_or_broken(title):
                send("🔥 FREE/BROKEN DEAL\n" + text)
                add_deal(text)
                continue

            # GARMIN
            if "garmin" in title and price and price <= 50:
                send("🛰 GARMIN DEAL\n" + text)
                add_deal(text)

            # BIKE
            elif "bike" in title or "velo" in title:
                if price and price <= 400 and score >= 70:
                    send("🚲 BIKE DEAL\n" + text)
                    add_deal(text)

            # MACBOOK
            elif "macbook" in title:
                if score >= 70:
                    send("💻 MACBOOK DEAL\n" + text)
                    add_deal(text)

    except Exception as e:
        print("RICARDO ERROR:", e)

# =========================
# TUTTI (BASIC SCRAPER SAFE)
# =========================

def search_tutti():
    try:
        r = requests.get(
            "https://www.tutti.ch/de/li/q/garmin-bike-macbook",
            headers=HEADERS,
            timeout=20
        )

        text = r.text.lower()

        if "garmin" in text and "bike" in text:
            print("TUTTI PAGE OK")

    except Exception as e:
        print("TUTTI ERROR:", e)

# =========================
# DAILY BEST DEALS
# =========================

def send_daily_deals():
    if not daily_deals:
        send("📉 Сегодня выгодных сделок не найдено")
        return

    sorted_deals = sorted(daily_deals, key=lambda x: len(x))[:3]

    msg = "🔥 TOP DEALS OF THE DAY\n\n" + "\n\n".join(sorted_deals)

    send(msg)

# =========================
# MONITOR
# =========================

def monitor():
    print("MONITOR STARTED")
    send("🟢 Smart Deal Bot started")

    last_day = time.time()

    while True:
        search_ricardo()
        search_tutti()

        # daily report
        if time.time() - last_day > 86400:
            send_daily_deals()
            daily_deals.clear()
            last_day = time.time()

        time.sleep(1800)

# =========================
# FLASK
# =========================

@app.route("/")
def home():
    return "bot running"

# =========================
# START
# =========================

if __name__ == "__main__":
    print("BOT STARTING")
    threading.Thread(target=monitor, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
