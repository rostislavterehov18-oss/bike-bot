```python
from flask import Flask
import requests
import threading
import time
import json
import os

TOKEN = "8793663575:AAGScR9IZhmB-N5sHQVpdhQmBGJwJXvBaYA"
CHANNEL_ID = "@swiss_bike"

API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

seen = set()
DB_FILE = "price_db.json"


def load_db():
    if not os.path.exists(DB_FILE):
        return []

    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data[-2000:], f)


price_db = load_db()


def send(text):
    try:
        r = requests.post(
            API_URL + "/sendMessage",
            json={
                "chat_id": CHANNEL_ID,
                "text": text,
                "disable_web_page_preview": False
            },
            timeout=15
        )

        print("SEND:", r.text)

    except Exception as e:
        print("SEND ERROR:", e)


def update_market(title, price):
    if price is None:
        return

    price_db.append({
        "title": title,
        "price": price,
        "time": time.time()
    })

    save_db(price_db)


def score(price_value):
    if price_value <= 50:
        return 95

    if price_value <= 100:
        return 80

    return 50


def search_ricardo():
    print("RICARDO SEARCH")

    # сюда потом можно добавить реальный поиск
    return []


def search_tutti():
    print("TUTTI SEARCH")

    # сюда потом можно добавить реальный поиск
    return []


def monitor():
    print("MONITOR STARTED")

    send("🟢 Бот запущен")

    last_alive = 0

    while True:

        try:
            print("SEARCH START")

            search_ricardo()
            search_tutti()

            if time.time() - last_alive > 3600:
                send("💚 Бот работает. Новых объявлений пока нет.")
                last_alive = time.time()

            print("SEARCH END")

        except Exception as e:
            print("MONITOR ERROR:", e)

        time.sleep(1800)


@app.route("/")
def home():
    return "bot running"


if __name__ == "__main__":
    print("BOT STARTING")

    threading.Thread(
        target=monitor,
        daemon=True
    ).start()

    app.run(
        host="0.0.0.0",
        port=10000
    )
```
