import os
import time
import threading
import requests
from flask import Flask
from bs4 import BeautifulSoup

# Environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TARGET_URL = os.environ.get("TARGET_URL", "https://www.rightmove.co.uk/property-to-rent/find/Clarion-Housing-Lettings/UK-58989.html")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 120))  # default: every 2 minutes

seen_ids = set()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=payload)
        print(f"[Telegram] Status: {response.status_code} | Response: {response.text}")
    except Exception as e:
        print(f"[Telegram Error] {e}")

def scrape_and_notify():
    global seen_ids
    while True:
        print(f"[Scraper] Checking listings at {TARGET_URL}")
        try:
            response = requests.get(TARGET_URL, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            listings = soup.select('div[data-testid^="propertyCard-"]')

            new_listings = []
            for listing in listings:
                link_tag = listing.select_one('a[href*="/properties/"]')
                price_tag = listing.select_one('[data-testid="property-price"]')
                address_tag = listing.select_one('[data-testid="property-address"]')

                if not link_tag:
                    continue

                href = link_tag['href']
                listing_id = href.split("/")[2].split("#")[0]
                if listing_id in seen_ids:
                    continue

                seen_ids.add(listing_id)
                full_url = f"https://www.rightmove.co.uk{href}"
                price = price_tag.get_text(strip=True) if price_tag else "No price"
                address = address_tag.get_text(strip=True) if address_tag else "No address"

                message = f"🏡 <b>New Listing Found!</b>\n📍 {address}\n💰 {price}\n🔗 <a href='{full_url}'>View Listing</a>"
                new_listings.append(message)

            if new_listings:
                print(f"[Scraper] Found {len(new_listings)} new listings")
                for msg in new_listings:
                    send_telegram_message(msg)
            else:
                print("[Scraper] No new listings")

        except Exception as e:
            print(f"[Scraper Error] {e}")
        time.sleep(CHECK_INTERVAL)

# Flask web server for Render uptime
app = Flask(__name__)

@app.route("/")
def home():
    return "Clarion Rightmove Bot is running!"

def start_bot():
    print("🔥 start_bot() has started running")
    thread = threading.Thread(target=scrape_and_notify)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    start_bot()
    app.run(host="0.0.0.0", port=10000)
