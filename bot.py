from flask import Flask, request
import requests
import threading
import time

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

CHAT_ID = None
seen = set()


# ----------------------------
def send_message(chat_id, text):
    try:
        requests.post(API_URL + "/sendMessage", json={
            "chat_id": chat_id,
            "text": text
        }, timeout=10)
    except:
        pass


# ----------------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ----------------------------
# RICARDO SEARCH
# ----------------------------
def search_ricardo():
    url = "https://www.ricardo.ch/api/search/v1/search"

    params = {
        "query": "Garmin Fahrrad bike",
        "limit": 20
    }

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=20)
        data = r.json()

        items = data.get("items", [])
        results = []

        for item in items:
            title = (item.get("title") or "").lower()
            price = item.get("price", None)
            link = item.get("url", "")

            if not link.startswith("http"):
                link = "https://www.ricardo.ch" + link

            if link in seen:
                continue

            # ----------------------------
            # 🛰 GARMIN 0-50 CHF
            # ----------------------------
            if "garmin" in title:
                if price is not None and 0 <= price <= 50:
                    seen.add(link)
                    results.append(f"🛰 Garmin (0-50 CHF)\n{title}\n{price} CHF\n{link}")

            # ----------------------------
            # 🚲 BIKES <= 200 CHF
            # ----------------------------
            bike_words = ["bike", "fahrrad", "velo"]

            if any(w in title for w in bike_words):
                if price is not None and price <= 200:
                    seen.add(link)
                    results.append(f"🚲 Bike (≤200 CHF)\n{title}\n{price} CHF\n{link}")

        return results

    except:
        return []


# ----------------------------
# TUTTI SEARCH
# ----------------------------
def search_tutti():
    url = "https://www.tutti.ch/api/v10/search"

    params = {
        "query": "garmin fahrrad bike",
        "limit": 20
    }

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=20)

        if "json" not in r.headers.get("Content-Type", ""):
            return []

        data = r.json()
        items = data.get("items", [])

        results = []

        for item in items:
            title = (item.get("title") or "").lower()
            price = item.get("price", 999999)
            link = item.get("url", "")

            if not link.startswith("http"):
                link = "https://www.tutti.ch" + link

            if link in seen:
                continue

            # ----------------------------
            # 🚲 FREE BIKES (GERMAN WORDS)
            # ----------------------------
            free_words = ["gratis", "kostenlos", "zu verschenken", "free"]

            if any(w in title for w in free_words):
                seen.add(link)
                results.append(f"🚲 FREE Bike\n{title}\n{link}")

            # ----------------------------
            # 🚲 BIKE ≤ 200 CHF
            # ----------------------------
            bike_words = ["bike", "fahrrad", "velo"]

            if any(w in title for w in bike_words):
                if price <= 200:
                    seen.add(link)
                    results.append(f"🚲 Bike (≤200 CHF)\n{title}\n{price} CHF\n{link}")

            # ----------------------------
            # 🛰 GARMIN 0-50
            # ----------------------------
            if "garmin" in title:
                if price <= 50:
                    seen.add(link)
                    results.append(f"🛰 Garmin (0-50 CHF)\n{title}\n{price} CHF\n{link}")

        return results

    except:
        return []


# ----------------------------
def search_all():
    return search_ricardo() + search_tutti()


# ----------------------------
def monitor():
    while True:
        try:
            if CHAT_ID:
                items = search_all()

                for i in items:
                    send_message(CHAT_ID, i)

            time.sleep(1800)  # 30 min

        except:
            time.sleep(60)


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
            send_message(CHAT_ID, "🛰 Монитор запущен\nGarmin 0-50 CHF + Bikes ≤200 CHF + Free bikes")

        elif text == "/check":
            items = search_all()

            send_message(CHAT_ID, "\n\n".join(items) if items else "❌ ничего не найдено")

    return "ok"


# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "Bot running"


# ----------------------------
if __name__ == "__main__":
    t = threading.Thread(target=monitor, daemon=True)
    t.start()

    app.run(host="0.0.0.0", port=10000)
