from flask import Flask
import threading
import time
import os
import requests
from playwright.sync_api import sync_playwright

# ======================
# CONFIG
# ======================

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

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
# FILTER LOGIC
# ======================

def is_good(title, price):
    title = title.lower()

    if price is None:
        return False

    if "garmin" in title and price <= 50:
        return True

    if any(x in title for x in ["bike", "velo"]) and price <= 400:
        return True

    if "gratis" in title or "free" in title or "defekt" in title:
        return True

    return False

# ======================
# SCRAPER (PLAYWRIGHT)
# ======================

def scrape_tutti(page):
    print("SCRAPE TUTTI")

    page.goto("https://www.tutti.ch/de/li/q/bike", timeout=60000)
    page.wait_for_timeout(5000)

    items = page.query_selector_all("article")

    for item in items[:20]:
        try:
            title_el = item.query_selector("h2, h3")
            price_el = item.query_selector("[data-testid='price']")

            title = title_el.inner_text() if title_el else ""
            price_text = price_el.inner_text() if price_el else ""

            price = None
            try:
                price = float("".join([c for c in price_text if c.isdigit()]))
            except:
                pass

            link_el = item.query_selector("a")
            link = link_el.get_attribute("href") if link_el else ""

            if link and not link.startswith("http"):
                link = "https://www.tutti.ch" + link

            if is_good(title, price):
                send(f"🚲 TUTTI DEAL\n{title}\n{price} CHF\n{link}")

        except Exception as e:
            print("ITEM ERROR:", e)

# ======================
# RICARDO SCRAPER
# ======================

def scrape_ricardo(page):
    print("SCRAPE RICARDO")

    page.goto("https://www.ricardo.ch/de/c/all?query=bike", timeout=60000)
    page.wait_for_timeout(5000)

    items = page.query_selector_all("article")

    for item in items[:20]:
        try:
            title_el = item.query_selector("h2, h3")
            price_el = item.query_selector("span")

            title = title_el.inner_text() if title_el else ""
            price_text = price_el.inner_text() if price_el else ""

            price = None
            try:
                price = float("".join([c for c in price_text if c.isdigit()]))
            except:
                pass

            link_el = item.query_selector("a")
            link = link_el.get_attribute("href") if link_el else ""

            if link and not link.startswith("http"):
                link = "https://www.ricardo.ch" + link

            if is_good(title, price):
                send(f"🛰 RICARDO DEAL\n{title}\n{price} CHF\n{link}")

        except Exception as e:
            print("ITEM ERROR:", e)

# ======================
# BOT LOOP
# ======================

def bot_loop():
    print("BOT STARTED")

    send("🟢 PLAYWRIGHT BOT STARTED")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        while True:
            try:
                print("SCAN START")

                scrape_tutti(page)
                scrape_ricardo(page)

                send("💚 SCAN DONE")

            except Exception as e:
                print("LOOP ERROR:", e)
                send("⚠️ ERROR IN LOOP")

            time.sleep(120)

# ======================
# FLASK
# ======================

@app.route("/")
def home():
    return "bot alive"

# ======================
# START
# ======================

if __name__ == "__main__":

    t = threading.Thread(target=bot_loop, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
