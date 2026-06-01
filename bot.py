from flask import Flask, request
import requests
import threading
import time

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

CHAT_ID = None
seen = set()

last_notify_time = 0


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
def parse_price(p):
    try:
        return float(p)
    except:
        return None


# ----------------------------
BIKE_WORDS = ["bike", "velo", "fahrrad"]
BROKEN_WORDS = ["defekt", "kaputt", "broken", "nicht funktioniert", "verschenke", "gratis", "for parts"]


def is_broken(text):
    return any(w in text for w in BROKEN_WORDS)


# ----------------------------
# 🛰 RICARDO (каждые 20 мин)
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

        for item in items:
            title = (item.get("title") or "").lower()
            link = item.get("url") or ""
            price = parse_price(item.get("price"))

            if not link.startswith("http"):
                link = "https://www.ricardo.ch" + link

            if link in seen:
                continue

            # 🛰 GARMIN ≤ 50
            if "garmin" in title and price is not None and price <= 50:
                seen.add(link)
                results.append(f"🛰 GARMIN ≤50 CHF\n{title}\n{price} CHF\n{link}")

            # 🚲 BIKE ≤ 400 + condition
            if any(w in title for w in BIKE_WORDS) and price is not None and price <= 400:
                if is_broken(title) or price <= 200:
                    seen.add(link)
                    results.append(f"🚲 BIKE\n{title}\n{price} CHF\n{link}")

        return results

    except:
        return []


# ----------------------------
# 🟡 TUTTI (каждые 30 мин — защита от блокировки)
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

        for item in items:
            title = (item.get("title") or "").lower()
            link = item.get("url") or ""
            price = parse_price(item.get("price"))

            if not link.startswith("http"):
                link = "https://www.tutti.ch" + link

            if link in seen:
                continue

            # 🛰 GARMIN
            if "garmin" in title and price is not None and price <= 50:
                seen.add(link)
                results.append(f"🛰 GARMIN ≤50 CHF\n{title}\n{price} CHF\n{link}")

            # 🚲 BIKE
            if any(w in title for w in BIKE_WORDS) and price is not None and price <= 400:
                if is_broken(title) or price <= 200:
                    seen.add(link)
                    results.append(f"🚲 BIKE\n{title}\n{price} CHF\n{link}")

        return results

    except:
        return []


# ----------------------------
def monitor_ricardo():
    while True:
        try:
            if CHAT_ID:
                items = search_ricardo()
                for i in items:
                    send(CHAT_ID, i)
            time.sleep(1200)  # 20 min
        except:
            time.sleep(60)


# ----------------------------
def monitor_tutti():
    while True:
        try:
            if CHAT_ID:
                items = search_tutti()
                for i in items:
                    send(CHAT_ID, i)
            time.sleep(1800)  # 30 min
        except:
            time.sleep(60)


# ----------------------------
# 💬 TELEGRAM
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
            send(CHAT_ID, "🟢 PRO монитор запущен")
            send(CHAT_ID, "🛰 Garmin ≤50 CHF | 🚲 Bikes ≤400 CHF | CH")

        elif text == "/status":
            send(CHAT_ID, "🟢 бот работает" if CHAT_ID else "🔴 нет чата")

        elif text == "/check":
            r = search_ricardo() + search_tutti()
            send(CHAT_ID, "\n\n".join(r) if r else "❌ ничего не найдено")

    return "ok"


# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "PRO monitor running"


# ----------------------------
if __name__ == "__main__":
    threading.Thread(target=monitor_ricardo, daemon=True).start()
    threading.Thread(target=monitor_tutti, daemon=True).start()

    app.run(host="0.0.0.0", port=10000)
