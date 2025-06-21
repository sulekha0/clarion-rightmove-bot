import os
import threading
import time
import requests
from flask import Flask
from bs4 import BeautifulSoup

# Load environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SELF_URL = os.environ.get("SELF_URL")
URL = "https://www.rightmove.co.uk/property-to-rent/find/Clarion-Housing-Lettings/UK.html?locationIdentifier=BRANCH%5E58989&propertyStatus=all&includeLetAgreed=true&_includeLetAgreed=on"

seen_links = set()
app = Flask(__name__)

def send_telegram(message):
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=10
        )
        print("📤 Telegram message sent:", message[:60])
    except Exception as e:
        print("❌ Telegram error:", e)

def get_new_listings():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(URL, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.find_all("div", class_="propertyCard")
        results = []

        for card in cards:
            try:
                link = card.find("a", class_="propertyCard-link")
                title = card.find("h2", class_="propertyCard-title")
                location = card.find("address", class_="propertyCard-address")
                price = card.find("div", class_="propertyCard-priceValue")

                if not all([link, title, location, price]):
                    continue

                href = "https://www.rightmove.co.uk" + link["href"]
                if href in seen_links:
                    continue

                seen_links.add(href)

                message = (
                    f"🏡 <b>{title.get_text(strip=True)}</b>\n"
                    f"📍 {location.get_text(strip=True)}\n"
                    f"💷 {price.get_text(strip=True)}\n"
                    f"📅 Just now\n"
                    f"🔗 {href}"
                )
                results.append(message)
            except Exception as e:
                print("⚠️ Error parsing a card:", e)
                continue

        return results
    except Exception as e:
        print("💥 Error scraping listings:", e)
        send_telegram(f"💥 Scraping error:\n{e}")
        return []

def start_bot():
    print("🔥 start_bot() has started running")
    send_telegram("🤖 Clarion bot is now running every 1 second...")

    while True:
        try:
            listings = get_new_listings()
            if listings:
                print(f"✅ Found {len(listings)} new listings.")
                for message in listings:
                    send_telegram(message)
            else:
                print("🕵️ No listings found this cycle.")
        except Exception as e:
            print("💥 Error in main loop:", e)
            send_telegram(f"💥 Bot crashed:\n{e}")
        time.sleep(1)

def self_ping():
    while True:
        try:
            requests.get(SELF_URL, timeout=5)
        except Exception as e:
            print("⚠️ Self-ping failed:", e)
            send_telegram(f"⚠️ Self-ping failed:\n{e}")
        time.sleep(300)

@app.route("/")
def home():
    return "✅ Clarion bot is alive and scanning every 1 second!"

if __name__ == "__main__":
    threading.Thread(target=start_bot).start()
    threading.Thread(target=self_ping).start()
    app.run(host="0.0.0.0", port=10000)
