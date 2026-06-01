from flask import Flask, request
import requests
import threading
import time

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

# ✅ ТВОЙ КАНАЛ
CHANNEL_ID = "@swiss_bike"

seen = set()


# ----------------------------
def send(text):
    try:
        r = requests.post(API_URL + "/sendMessage", json={
            "chat_id": CHANNEL_ID,
            "text": text,
            "disable_web_page_preview": False
        }, timeout=10)

        print("SEND:", r.text)

    except Exception as e:
        print("SEND ERROR:", e)


HEADERS = {"User-Agent": "Mozilla/5.0"}


# ----------------------------
def parse_price(p):
    try:
        return float(p)
    except:
        return None


# ----------------------------
# 🚲 SEARCH LOGIC
# ----------------------------
def search():
    try:
        r = requests.get(
            "https://www.ricardo.ch/api/search/v1/search",
            params={"query": "garmin bike velo fahrrad defekt kaputt gratis", "limit": 30},
            headers=HEADERS,
            timeout=20
        )

        data = r.json()
        items = data.get("items", [])

        results = []

        for i in items:
            title = (i.get("title") or "").lower()
            link = i.get("url") or ""
            price = parse_price(i.get("price"))

            if not link.startswith("http"):
                link = "https://www.ricardo.ch" + link

            if link in seen:
                continue

            # 🛰 GARMIN ≤ 50 CHF
            if "garmin" in title and price is not None and price <= 50:
                seen.add(link)
                results.append(f"🛰 GARMIN DEAL\n{title}\n{price} CHF\n{link}")

            # 🚲 BIKE ≤ 400 CHF
            elif ("bike" in title or "velo" in title or "fahrrad" in title) and price is not None and price <= 400:
                if "defekt" in title or "kaputt" in title or price <= 200:
                    seen.add(link)
                    results.append(f"🚲 BIKE DEAL\n{title}\n{price} CHF\n{link}")

        return results

    except Exception as e:
        print("SEARCH ERROR:", e)
        return []


# ----------------------------
def monitor():
    while True:
        try:
            items = search()

            if items:
                for i in items:
                    send(i)
            else:
                print("NO NEW ITEMS")

            time.sleep(1800)  # 30 минут

        except Exception as e:
            print("MONITOR ERROR:", e)
            time.sleep(60)


# ----------------------------
@app.route("/", methods=["GET"])
def home():
    return "swiss bike bot running"


# ----------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if data and "message" in data:
        text = data["message"].get("text", "")
        chat_id = data["message"]["chat"]["id"]

        if text == "/start":
            requests.post(API_URL + "/sendMessage", json={
                "chat_id": chat_id,
                "text": "🟢 Монитор запущен: Garmin + Bikes (CH deals)"
            })

    return "ok"


# ----------------------------
if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
