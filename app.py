import requests
from bs4 import BeautifulSoup
import time
import threading
from flask import Flask
import datetime
import os

# === CONFIG ===
URL = "https://www.rightmove.co.uk/property-to-rent/find/Clarion-Housing-Lettings/UK.html?locationIdentifier=BRANCH%5E58989&propertyStatus=all&includeLetAgreed=true&_includeLetAgreed=on"
CHECK_INTERVAL = 1  # seconds
SELF_PING_INTERVAL = 300  # 5 minutes

# === ENV VARIABLES ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SELF_URL = os.getenv("SELF_URL")

seen_links = set()
last_listing_time = datetime.datetime.now()

# === TELEGRAM ALERT ===
def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Missing TELEGRAM_TOKEN or CHAT_ID.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# === RIGHTMOVE SCRAPER ===
def get_new_listings():
    headers = {"User-Agent": "Mozilla/5.0"}
    for attempt in range(3):
        try:
            res = requests.get(URL, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select(".propertyCard")
            new = []
            for card in cards:
                link_tag = card.select_one("a.propertyCard-link")
                if link_tag and "href" in link_tag.attrs:
                    href = "https://www.rightmove.co.uk" + link_tag["href"]
                    if href in seen_links:
                        continue
                    seen_links.add(href)

                    title = card.select_one(".propertyCard-title")
                    price = card.select_one(".propertyCard-priceValue")
                    location = card.select_one(".propertyCard-address")
                    date_added = card.select_one(".propertyCard-branchSummary-addedOrReduced")

                    title_text = title.get_text(strip=True) if title else "N/A"
                    price_text = price.get_text(strip=True) if price else "N/A"
                    location_text = location.get_text(strip=True) if location else "N/A"
                    date_text = date_added.get_text(strip=True) if date_added else "Date not found"

                    message = (
                        f"🏡 <b>{title_text}</b>\n"
                        f"📍 {location_text}\n"
                        f"💷 {price_text}\n"
                        f"📅 {date_text}\n"
                        f"🔗 <a href='{href}'>View Listing</a>"
                    )
                    new.append(message)
            return new
        except Exception as e:
            if attempt == 2:
                send_telegram(f"⚠️ Failed after 3 attempts:\n{e}")
            time.sleep(1)
    return []

# === BOT LOOP ===
def start_bot():
    global last_listing_time
    send_telegram("🤖 Clarion bot is now running every 1 second...")
    while True:
        new_listings = get_new_listings()
        if new_listings:
            last_listing_time = datetime.datetime.now()
            for msg in new_listings:
                send_telegram(msg)

        minutes_since = (datetime.datetime.now() - last_listing_time).total_seconds() / 60
        if minutes_since > 180:
            send_telegram("⚠️ No new listings in 3+ hours. Bot still running.")
            last_listing_time = datetime.datetime.now()
        time.sleep(CHECK_INTERVAL)

# === SELF-PING LOOP ===
def start_self_ping():
    while True:
        try:
            if SELF_URL:
                requests.get(SELF_URL, timeout=10)
        except Exception as e:
            print(f"Self-ping error: {e}")
        time.sleep(SELF_PING_INTERVAL)

# === FLASK APP ===
app = Flask(__name__)
@app.route('/')
def home():
    return "✅ Clarion bot is alive and scanning every 1 second!"

# === START EVERYTHING ===
if __name__ == "__main__":
    threading.Thread(target=start_bot).start()
    threading.Thread(target=start_self_ping).start()
    app.run(host="0.0.0.0", port=10000)
