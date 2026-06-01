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
# 💡 УМНАЯ ОЦЕНКА ЦЕНЫ
# ----------------------------
def price_score(price, base):
    if price is None:
        return "❓ неизвестно"

    ratio = price / base

    if ratio <= 0.6:
        return "🔥 ОЧЕНЬ ВЫГОДНО"
    elif ratio <= 0.9:
        return "👍 норм цена"
    else:
        return "❌ дорого"


# ----------------------------
# RICARDO SMART SEARCH
# ----------------------------
def search_ricardo():
    try:
        r = requests.get(
            "https://www.ricardo.ch/api/search/v1/search",
            params={"query": "garmin bike velo fahrrad", "limit": 20},
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

            # ----------------------------
            # 🛰 GARMIN
            # ----------------------------
            if "garmin" in title:
                base = 80
                score = price_score(price, base)

                if price is not None and price <= 50:
                    seen.add(link)
                    results.append(
                        f"🛰 GARMIN\n"
                        f"{title}\n"
                        f"Цена: {price} CHF\n"
                        f"Оценка: {score}\n"
                        f"{link}"
                    )

            # ----------------------------
            # 🚲 BIKE
            # ----------------------------
            if any(x in title for x in ["bike", "velo", "fahrrad"]):
                base = 500
                score = price_score(price, base)

                if price is not None and price <= 400:
                    # только если не дорого
                    if score != "❌ дорого":
                        seen.add(link)
                        results.append(
                            f"🚲 BIKE\n"
                            f"{title}\n"
                            f"Цена: {price} CHF\n"
                            f"Оценка: {score}\n"
                            f"{link}"
                        )

        return results

    except:
        return []


# ----------------------------
# TUTTI SMART SEARCH
# ----------------------------
def search_tutti():
    try:
        r = requests.get(
            "https://www.tutti.ch/api/v10/search",
            params={"query": "garmin bike velo gratis", "limit": 20},
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

            # ----------------------------
            # 🛰 GARMIN
            # ----------------------------
            if "garmin" in title:
                base = 80
                score = price_score(price, base)

                if price is not None and price <= 50:
                    seen.add(link)
                    results.append(
                        f"🛰 GARMIN\n"
                        f"{title}\n"
                        f"{price} CHF\n"
                        f"{score}\n"
                        f"{link}"
                    )

            # ----------------------------
            # 🚲 FREE BIKES
            # ----------------------------
            if any(x in title for x in ["gratis", "kostenlos", "verschenke"]):
                seen.add(link)
                results.append(f"🚲 FREE BIKE\n{title}\n{link}")

            # ----------------------------
            # 🚲 BIKE ≤400
            # ----------------------------
            if any(x in title for x in ["bike", "velo", "fahrrad"]):
                base = 500
                score = price_score(price, base)

                if price is not None and price <= 400:
                    if score != "❌ дорого":
                        seen.add(link)
                        results.append(
                            f"🚲 BIKE\n"
                            f"{title}\n"
                            f"{price} CHF\n"
                            f"{score}\n"
                            f"{link}"
                        )

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
        CHAT_ID = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_message(CHAT_ID, "🧠 Smart монитор запущен\nGarmin + Bikes + AI оценка")

        elif text == "/check":
            items = search_all()
            send_message(CHAT_ID, "\n\n".join(items) if items else "❌ ничего не найдено")

    return "ok"


# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "Smart bot running"


# ----------------------------
if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
