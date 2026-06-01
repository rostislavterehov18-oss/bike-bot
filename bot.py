from flask import Flask, request
import requests
import threading
import time

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

CHAT_ID = None
seen = set()
MONITOR_RUNNING = False


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
def safe_float(val):
    try:
        return float(val)
    except:
        return None


# ----------------------------
# 🧠 УМНАЯ ОЦЕНКА
# ----------------------------
def price_score(price, base):
    if price is None:
        return "❓"

    ratio = price / base

    if ratio <= 0.6:
        return "🔥 выгодно"
    elif ratio <= 0.9:
        return "👍 норм"
    else:
        return "❌ дорого"


# ----------------------------
# 🛰 RICARDO STRICT
# ----------------------------
def search_ricardo_strict():
    try:
        r = requests.get(
            "https://www.ricardo.ch/api/search/v1/search",
            params={"query": "garmin bike velo fahrrad navigation", "limit": 20},
            headers=HEADERS,
            timeout=20
        )

        data = r.json()
        items = data.get("items", [])

        results = []

        for item in items:
            title = (item.get("title") or "").lower()
            link = item.get("url") or ""
            price = safe_float(item.get("price"))

            if not link.startswith("http"):
                link = "https://www.ricardo.ch" + link

            if link in seen:
                continue

            # 🛰 Garmin
            if "garmin" in title and price and price <= 50:
                seen.add(link)
                results.append(f"🛰 Garmin ≤50 CHF\n{title}\n{price} CHF | {price_score(price, 80)}\n{link}")

            # 🚲 Bike
            if any(x in title for x in ["bike", "velo", "fahrrad"]) and price and price <= 400:
                seen.add(link)
                results.append(f"🚲 Bike ≤400 CHF\n{title}\n{price} CHF | {price_score(price, 500)}\n{link}")

            # 🆓 Free
            if any(x in title for x in ["gratis", "kostenlos", "verschenke", "free"]):
                seen.add(link)
                results.append(f"🆓 FREE\n{title}\n{link}")

        return results

    except:
        return []


# ----------------------------
# 🟡 RICARDO LOOSE
# ----------------------------
def search_ricardo_loose():
    try:
        r = requests.get(
            "https://www.ricardo.ch/api/search/v1/search",
            params={"query": "garmin bike velo fahrrad", "limit": 30},
            headers=HEADERS,
            timeout=20
        )

        data = r.json()
        items = data.get("items", [])

        results = []

        for item in items:
            title = (item.get("title") or "").lower()
            link = item.get("url") or ""

            if not link.startswith("http"):
                link = "https://www.ricardo.ch" + link

            if link in seen:
                continue

            if any(x in title for x in ["garmin", "bike", "velo", "fahrrad"]):
                seen.add(link)
                results.append(f"🟡 LOOSE\n{title}\n{link}")

        return results

    except:
        return []


# ----------------------------
# 🟢 TUTTI STRICT
# ----------------------------
def search_tutti_strict():
    try:
        r = requests.get(
            "https://www.tutti.ch/api/v10/search",
            params={"query": "garmin bike velo gratis verschenken", "limit": 20},
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
            price = safe_float(item.get("price"))

            if not link.startswith("http"):
                link = "https://www.tutti.ch" + link

            if link in seen:
                continue

            if "garmin" in title and price and price <= 50:
                seen.add(link)
                results.append(f"🛰 Garmin ≤50 CHF\n{title}\n{price} CHF\n{link}")

            if any(x in title for x in ["bike", "velo", "fahrrad"]) and price and price <= 400:
                seen.add(link)
                results.append(f"🚲 Bike ≤400 CHF\n{title}\n{price} CHF\n{link}")

            if any(x in title for x in ["gratis", "kostenlos", "verschenke"]):
                seen.add(link)
                results.append(f"🆓 FREE\n{title}\n{link}")

        return results

    except:
        return []


# ----------------------------
# 🟡 TUTTI LOOSE
# ----------------------------
def search_tutti_loose():
    try:
        r = requests.get(
            "https://www.tutti.ch/api/v10/search",
            params={"query": "garmin bike velo", "limit": 30},
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

            if not link.startswith("http"):
                link = "https://www.tutti.ch" + link

            if link in seen:
                continue

            if any(x in title for x in ["garmin", "bike", "velo"]):
                seen.add(link)
                results.append(f"🟡 LOOSE\n{title}\n{link}")

        return results

    except:
        return []


# ----------------------------
def search_all():
    results = search_ricardo_strict() + search_tutti_strict()

    # 🔥 если пусто → ослабляем фильтр
    if not results:
        results = search_ricardo_loose() + search_tutti_loose()

    return results


# ----------------------------
def monitor():
    global MONITOR_RUNNING
    MONITOR_RUNNING = True

    while True:
        try:
            if CHAT_ID:
                items = search_all()

                if items:
                    for i in items:
                        send_message(CHAT_ID, i)
                else:
                    send_message(CHAT_ID, "❌ нет новых выгодных объявлений")

            time.sleep(1800)

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
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        CHAT_ID = chat_id

        if text == "/start":
            send_message(chat_id, "🟢 Бот жив")
            send_message(chat_id, "🧠 Smart монитор активен")

        elif text == "/status":
            send_message(chat_id, f"🟢 работает" if MONITOR_RUNNING else "🔴 не запущен")

        elif text == "/check":
            items = search_all()
            send_message(chat_id, "\n\n".join(items) if items else "❌ ничего не найдено")

    return "ok"


# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "Adaptive bot running"


# ----------------------------
if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
