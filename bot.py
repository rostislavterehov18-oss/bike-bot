from flask import Flask
import requests
import threading
import time
from bs4 import BeautifulSoup

# ======================
# CONFIG
# ======================

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

seen = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

# ======================
# SEND TELEGRAM
# ======================

def send(text):
    try:
        r = requests.post(API_URL + "/sendMessage", json={
            "chat_id": CHANNEL_ID,
            "text": text
        }, timeout=15)

        print("SEND:", r.text)

    except Exception as e:
        print("SEND ERROR:", e)

# ======================
# RICARDO (OFFICIAL API STYLE)
# ======================

def search_ricardo():
    try:
        url = "https://www.ricardo.ch/api/search/v1/search"

        params = {
            "query": "garmin bike macbook velo apple",
            "limit": 20
        }

        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        data = r.json()

        items = data.get("items", [])

        for item in items:
            title = (item.get("title") or "").lower()
            price = item.get("price")
            link = item.get("url")

            if not link:
                continue

            if link in seen:
                continue

            seen.add(link)

            if "garmin" in title and price and price <= 50:
                send(f"🛰 GARMIN\n{title}\n{price} CHF\n{link}")

            if any(x in title for x in ["bike", "velo"]) and price and price <= 400:
                send(f"🚲 BIKE\n{title}\n{price} CHF\n{link}")

            if "macbook" in title and price and price <= 1500:
                send(f"💻 MACBOOK\n{title}\n{price} CHF\n{link}")

    except Exception as e:
        print("RICARDO ERROR:", e)

# ======================
# TUTTI SCRAPER (HTML)
# ======================

def search_tutti():
    try:
        url = "https://www.tutti.ch/de/li/q/garmin-bike-macbook"

        r = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        items = soup.select("article")

        for item in items:
            try:
                title = item.get_text().lower()
                link_tag = item.find("a")

                if not link_tag:
                    continue

                link = "https://www.tutti.ch" + link_tag["href"]

                if link in seen:
                    continue

                price = None

                price_tag = item.find(text=lambda x: x and "CHF" in x)
                if price_tag:
                    try:
                        price = float(price_tag.replace("CHF", "").replace("’", "").strip())
                    except:
                        pass

                seen.add(link)

                if "garmin" in title and price and price <= 50:
                    send(f"🛰 GARMIN (TUTTI)\n{title}\n{price} CHF\n{link}")

                if any(x in title for x in ["bike", "velo"]) and price and price <= 400:
                    send(f"🚲 BIKE (TUTTI)\n{title}\n{price} CHF\n{link}")

                if "macbook" in title:
                    send(f"💻 MACBOOK (TUTTI)\n{title}\n{price} CHF\n{link}")

            except:
                continue

    except Exception as e:
        print("TUTTI ERROR:", e)

# ======================
# MONITOR LOOP
# ======================

def monitor():
    print("MONITOR STARTED")
    send("🟢 Bot started")

    while True:
        print("SEARCH RUN")

        search_ricardo()
        search_tutti()

        time.sleep(1800)

# ======================
# FLASK
# ======================

@app.route("/")
def home():
    return "bot running"

# ======================
# START
# ======================

if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
