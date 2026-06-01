from flask import Flask
import threading
import time
import os
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ======================
# CONFIG
# ======================

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

seen = set()

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
        print("SEND:", text)
    except Exception as e:
        print("SEND ERROR:", e)

# ======================
# FILTER LOGIC (ВАЖНО)
# ======================

def is_good(title, price):
    title = title.lower()

    if price is None:
        return False

    # 🛰 Garmin
    if "garmin" in title and price <= 50:
        return True

    # 🚲 Bikes / Velo
    if ("bike" in title or "velo" in title) and price <= 400:
        return True

    # 💸 cheap deals
    if any(x in title for x in ["defekt", "kaputt", "gratis", "free", "billig"]):
        return True

    return False

# ======================
# SAFE PRICE PARSE
# ======================

def parse_price(text):
    if not text:
        return None
    digits = "".join([c for c in text if c.isdigit()])
    try:
        return float(digits)
    except:
        return None

# ======================
# SCRAPE TUTTI
# ======================

def scrape_tutti(page):
    print("SCRAPING TUTTI")

    try:
        page.goto("https://www.tutti.ch/de/li/ganze-schweiz?query=bike", timeout=60000)
        page.wait_for_timeout(5000)

        cards = page.query_selector_all("article")

        for c in cards[:30]:
            try:
                title_el = c.query_selector("h2, h3")
                price_el = c.query_selector("[data-testid*='price'], span")

                title = title_el.inner_text() if title_el else ""
                price = parse_price(price_el.inner_text() if price_el else "")

                link_el = c.query_selector("a")
                link = link_el.get_attribute("href") if link_el else ""

                if link and not link.startswith("http"):
                    link = "https://www.tutti.ch" + link

                key = link + str(price)

                if key in seen:
                    continue

                if is_good(title, price):
                    seen.add(key)
                    send(f"🚲 TUTTI DEAL\n{title}\n{price} CHF\n{link}")

            except:
                continue

    except PlaywrightTimeout:
        print("TUTTI TIMEOUT")

# ======================
# SCRAPE RICARDO
# ======================

def scrape_ricardo(page):
    print("SCRAPING RICARDO")

    try:
        page.goto("https://www.ricardo.ch/de/c/all?query=bike", timeout=60000)
        page.wait_for_timeout(5000)

        cards = page.query_selector_all("article")

        for c in cards[:30]:
            try:
                title_el = c.query_selector("h2, h3")
                price_el = c.query_selector("span")

                title = title_el.inner_text() if title_el else ""
                price = parse_price(price_el.inner_text() if price_el else "")

                link_el = c.query_selector("a")
                link = link_el.get_attribute("href") if link_el else ""

                if link and not link.startswith("http"):
                    link = "https://www.ricardo.ch" + link

                key = link + str(price)

                if key in seen:
                    continue

                if is_good(title, price):
                    seen.add(key)
                    send(f"🛰 RICARDO DEAL\n{title}\n{price} CHF\n{link}")

            except:
                continue

    except PlaywrightTimeout:
        print("RICARDO TIMEOUT")

# ======================
# MAIN LOOP
# ======================

def bot_loop():
    print("🚀 PLAYWRIGHT PRO v2 STARTED")
    send("🟢 PLAYWRIGHT PRO v2 STARTED")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = browser.new_page()

        while True:
            try:
                print("=== SCAN START ===")

                scrape_tutti(page)
                scrape_ricardo(page)

                send("💚 SCAN DONE - PRO v2")

            except Exception as e:
                print("LOOP ERROR:", e)

            time.sleep(120)

# ======================
# FLASK (Render requirement)
# ======================

@app.route("/")
def home():
    return "PLAYWRIGHT PRO v2 RUNNING"

# ======================
# START
# ======================

if __name__ == "__main__":
    t = threading.Thread(target=bot_loop, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
