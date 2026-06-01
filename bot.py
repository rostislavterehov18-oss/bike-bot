from flask import Flask
import requests
import threading
import time
import re

# ======================
# CONFIG
# ======================

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

seen = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "de-CH,de;q=0.9,en;q=0.8"
}

# ======================
# TELEGRAM
# ======================

def send(text):
    try:
        requests.post(
            API_URL + "/sendMessage",
            json={"chat_id": CHANNEL_ID, "text": text},
            timeout=10
        )
        print("SEND OK")
    except Exception as e:
        print("SEND ERROR:", e)

# ======================
# FILTER
# ======================

def is_good(title, price):
    if price is None:
        return False

    t = title.lower()

    if "garmin" in t and price <= 50:
        return True

    if ("bike" in t or "velo" in t) and price <= 400:
        return True

    if "macbook" in t and price <= 1500:
        return True

    return False

# ======================
# PRICE PARSER
# ======================

def extract_price(text):
    if not text:
        return None

    match = re.search(r'(\d{1,5})\s*(fr|chf|.-)', text.lower())
    if match:
        return int(match.group(1))

    return None

# ======================
# RICARDO HTML SEARCH
# ======================

def search_ricardo():
    try:
        print("RICARDO SEARCH...")

        url = "https://www.ricardo.ch/de/c/all?query=garmin%20bike%20velo%20macbook"

        r = requests.get(url, headers=HEADERS, timeout=20)

        if r.status_code != 200:
            print("RICARDO BLOCK:", r.status_code)
            return

        html = r.text

        # грубый парсинг ссылок
        links = re.findall(r'href="(/de/a/[^"]+)"', html)

        print("RICARDO LINKS:", len(links))

        for l in links[:30]:
            full = "https://www.ricardo.ch" + l

            if full in seen:
                continue

            seen.add(full)

            # получаем страницу товара
            r2 = requests.get(full, headers=HEADERS, timeout=15)

            title_match = re.search(r'<title>(.*?)</title>', r2.text)
            title = title_match.group(1) if title_match else "item"

            price = extract_price(r2.text)

            print("RICARDO ITEM:", title, price)

            if is_good(title, price):
                send(f"🔥 RICARDO DEAL\n{title}\n{price} CHF\n{full}")

    except Exception as e:
        print("RICARDO ERROR:", e)

# ======================
# TUTTI HTML SEARCH
# ======================

def search_tutti():
    try:
        print("TUTTI SEARCH...")

        url = "https://www.tutti.ch/de/li/q/bike-velo-garmin-macbook"

        r = requests.get(url, headers=HEADERS, timeout=20)

        if r.status_code == 403:
            print("TUTTI BLOCKED (403)")
            return

        if r.status_code != 200:
            print("TUTTI ERROR:", r.status_code)
            return

        html = r.text

        links = re.findall(r'href="(/de/vi/[^"]+)"', html)

        print("TUTTI LINKS:", len(links))

        for l in links[:30]:
            full = "https://www.tutti.ch" + l

            if full in seen:
                continue

            seen.add(full)

            r2 = requests.get(full, headers=HEADERS, timeout=15)

            title_match = re.search(r'<title>(.*?)</title>', r2.text)
            title = title_match.group(1) if title_match else "item"

            price = extract_price(r2.text)

            print("TUTTI ITEM:", title, price)

            if is_good(title, price):
                send(f"🚲 TUTTI DEAL\n{title}\n{price} CHF\n{full}")

    except Exception as e:
        print("TUTTI ERROR:", e)

# ======================
# MONITOR LOOP
# ======================

def monitor():
    print("BOT STARTED")

    send("🟢 BOT HTML SCRAPER STARTED")

    while True:
        try:
            search_ricardo()
            search_tutti()

        except Exception as e:
            print("MONITOR ERROR:", e)

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
