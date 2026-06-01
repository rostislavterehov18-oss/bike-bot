from flask import Flask, request
import requests
import threading
import time
from datetime import datetime

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

CHAT_ID = None
seen = set()

all_found = []  # 🔥 для топ дня


# ----------------------------
def send(chat_id, text):
    try:
        requests.post(API_URL + "/sendMessage", json={
            "chat_id": chat_id,
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
# 🧠 ОЦЕНКА ВЫГОДЫ
# ----------------------------
def score(title, price):
    t = title.lower()

    base = 500

    if "garmin" in t:
        base = 100
    if any(x in t for x in ["bike", "velo", "fahrrad"]):
        base = 600

    if "defekt" in t or "kaputt" in t:
        base *= 1.5

    if price is None:
        return 50

    s = max(0, int(100 - (price / base) * 100))

    return min(100, s)


# ----------------------------
BIKE_WORDS = ["bike", "velo", "fahrrad"]


# ----------------------------
def add_item(title, price_val, link, tag):
    global all_found

    s = score(title, price_val)

    item = {
        "title": title,
        "price": price_val,
        "link": link,
        "score": s,
        "tag": tag
    }

    all_found.append(item)


# ----------------------------
# 🛰 RICARDO
# ----------------------------
def search_ricardo():
    try:
        r = requests.get(
            "https://www.ricardo.ch/api/search/v1/search",
            params={"query": "garmin bike velo fahrrad defekt kaputt", "limit": 30},
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

            if "garmin" in title and p and p <= 50:
                seen.add(link)
                add_item(title, p, link, "GARMIN")
                results.append(f"🛰 Garmin\n{title}\n{p} CHF\n{link}")

            elif any(x in title for x in BIKE_WORDS) and p and p <= 400:
                if "defekt" in title or p <= 200:
                    seen.add(link)
                    add_item(title, p, link, "BIKE")
                    results.append(f"🚲 Bike\n{title}\n{p} CHF\n{link}")

        return results

    except:
        return []


# ----------------------------
def search_tutti():
    try:
        r = requests.get(
            "https://www.tutti.ch/api/v10/search",
            params={"query": "garmin bike velo fahrrad defekt kaputt gratis", "limit": 30},
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
                add_item(title, p, link, "GARMIN")
                results.append(f"🛰 Garmin\n{title}\n{p} CHF\n{link}")

            elif any(x in title for x in BIKE_WORDS) and (p is None or p <= 400):
                if "defekt" in title or p == 0:
                    seen.add(link)
                    add_item(title, p, link, "BIKE")
                    results.append(f"🚲 Bike\n{title}\n{p} CHF\n{link}")

        return results

    except:
        return []


# ----------------------------
def search_all():
    return search_ricardo() + search_tutti()


# ----------------------------
# 🔁 MONITOR RICARDO (20 min)
# ----------------------------
def monitor_ricardo():
    while True:
        if CHAT_ID:
            items = search_ricardo()
            for i in items:
                send(CHAT_ID, i)
        time.sleep(1200)


# ----------------------------
# 🔁 MONITOR TUTTI (30 min)
# ----------------------------
def monitor_tutti():
    while True:
        if CHAT_ID:
            items = search_tutti()
            for i in items:
                send(CHAT_ID, i)
        time.sleep(1800)


# ----------------------------
# 🏆 DAILY TOP DEALS
# ----------------------------
def top_deals_loop():
    global all_found

    while True:
        time.sleep(86400)  # 24h

        if CHAT_ID and all_found:

            sorted_items = sorted(all_found, key=lambda x: x["score"], reverse=True)[:10]

            msg = "🏆 TOP DEALS OF THE DAY\n\n"

            for i in sorted_items:
                msg += f"{i['tag']} | {i['score']}/100\n{i['title']}\n{i['price']} CHF\n{i['link']}\n\n"

            send(CHAT_ID, msg)

            all_found = []  # reset day


# ----------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    global CHAT_ID

    data = request.get_json()
    if not data:
        return "ok"

    if "message" in data:
        CHAT_ID = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send(CHAT_ID, "🟢 PRO монитор + AI рейтинг запущен")
            send(CHAT_ID, "🚲 Bikes ≤400 CHF | 🛰 Garmin ≤50 CHF")

        elif text == "/check":
            send(CHAT_ID, "\n\n".join(search_all()) or "❌ ничего не найдено")

        elif text == "/status":
            send(CHAT_ID, "🟢 работает")

    return "ok"


# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "TOP DEAL BOT RUNNING"


# ----------------------------
if __name__ == "__main__":
    threading.Thread(target=monitor_ricardo, daemon=True).start()
    threading.Thread(target=monitor_tutti, daemon=True).start()
    threading.Thread(target=top_deals_loop, daemon=True).start()

    app.run(host="0.0.0.0", port=10000)
