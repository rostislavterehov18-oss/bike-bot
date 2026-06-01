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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122 Safari/537.36"
}


# ----------------------------
# 🧠 ОЦЕНКА ЦЕНЫ
# ----------------------------
def price_score(price, base):
    if price is None:
        return "❓ неизвестно"

    ratio = price / base

    if ratio <= 0.6:
        return "🔥 выгодно"
    elif ratio <= 0.9:
        return "👍 нормально"
    else:
        return "❌ дорого"


# ----------------------------
# 🛰 RICARDO SEARCH
# ----------------------------
def search_ricardo():
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

            price = item.get("price")
            try:
                price = float(price)
            except:
                price = None

            if not link.startswith("http"):
                link = "https://www.ricardo.ch" + link

            if link in seen:
                continue

            # 🛰 GARMIN
            if "garmin" in title and price is not None and price <= 50:
                seen.add(link)
                results.append(
                    f"🛰 GARMIN ≤50 CHF\n"
                    f"{title}\n"
                    f"{price} CHF | {price_score(price, 80)}\n"
                    f"{link}"
                )

            # 🚲 BIKE
            if any(x in title for x in ["bike", "velo", "fahrrad"]) and price is not None and price <= 400:
                seen.add(link)
                results.append(
                    f"🚲 BIKE ≤400 CHF\n"
                    f"{title}\n"
                    f"{price} CHF | {price_score(price, 500)}\n"
                    f"{link}"
                )

            # 🆓 FREE
            if any(x in title for x in ["gratis", "kostenlos", "verschenke", "free"]):
                seen.add(link)
                results.append(f"🆓 FREE\n{title}\n{link}")

        return results

    except:
        return []


# ----------------------------
# 🟡 TUTTI SEARCH (SAFE)
# ----------------------------
def search_tutti():
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

            price = item.get("price")
            try:
                price = float(price)
            except:
                price = None

            if not link.startswith("http"):
                link = "https://www.tutti.ch" + link

            if link in seen:
                continue

            # 🛰 GARMIN
            if "garmin" in title and price is not None and price <= 50:
                seen.add(link)
                results.append(f"🛰 GARMIN ≤50 CHF\n{title}\n{price} CHF\n{link}")

            # 🚲 BIKE
            if any(x in title for x in ["bike", "velo", "fahrrad"]) and price is not None and price <= 400:
                seen.add(link)
                results.append(
                    f"🚲 BIKE ≤400 CHF\n{title}\n{price} CHF\n{link}"
                )

            # 🆓 FREE
            if any(x in title for x in ["gratis", "kostenlos", "verschenke"]):
                seen.add(link)
                results.append(f"🆓 FREE\n{title}\n{link}")

        return results

    except:
        return []


# ----------------------------
def search_all():
    return search_ricardo() + search_tutti()


# ----------------------------
# 🔁 MONITOR LOOP
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
                    send_message(CHAT_ID, "❌ новых выгодных объявлений нет")

            time.sleep(1800)

        except:
            time.sleep(60)


# ----------------------------
# 📩 WEBHOOK
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

        # 🟢 START
        if text == "/start":
            send_message(chat_id, "🟢 Бот жив и запущен")
            send_message(chat_id, "🧠 Монитор: Garmin + Bikes + Free (CH)")

        # 📡 STATUS
        elif text == "/status":
            status = "🟢 работает" if MONITOR_RUNNING else "🔴 не запущен"
            send_message(chat_id, f"Статус: {status}")

        # 🔍 CHECK
        elif text == "/check":
            items = search_all()
            send_message(chat_id, "\n\n".join(items) if items else "❌ ничего не найдено")

    return "ok"


# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "Smart monitor running"


# ----------------------------
if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
