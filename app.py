import os
import threading
import time
import requests
from flask import Flask
from bs4 import BeautifulSoup

# === Configuration ===
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SELF_URL = os.environ.get("SELF_URL")
TEST_MODE = False  # Set to True to use test HTML file

# === Rightmove URL ===
URL = "https://www.rightmove.co.uk/property-to-rent/find/Clarion-Housing-Lettings/UK-58989.html"

seen_ids = set()
app = Flask(__name__)

# === Telegram Function ===
def send_telegram(text):
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        }
        res = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data=payload,
            timeout=10
        )
        print(f"📤 Sent message: {text[:60]}")
    except Exception as e:
        print("❌ Telegram error:", e)

# === Scraper Function ===
def scrape_listings():
    print("[Scraper] Checking listings...")

    try:
        if TEST_MODE:
            with open("test_listing.html", "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
            print("[Scraper] Using test HTML file.")
        else:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(URL, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            # 👇 Save live HTML to inspect later
            with open("live_output.html", "w", encoding="utf-8") as f:
                f.write(soup.prettify())
            print("[Scraper] Live HTML saved to 'live_output.html'")

        listings = soup.find_all("div", class_="PropertyCard_propertyCardContainer__VSRSA")
        new_count = 0

        for listing in listings:
            link_tag = listing.find("a", href=True)
            if not link_tag:
                continue

            href = link_tag["href"]
            property_id = href.split("/")[2].split("#")[0]
            if property_id in seen_ids:
                continue

            seen_ids.add(property_id)
            new_count += 1

            full_link = "https://www.rightmove.co.uk" + href
            address_tag = listing.find("address")
            price_tag = listing.find("div", class_="PropertyPrice_price__VL65t")

            address = address_tag.get_text(strip=True) if address_tag else "No address"
            price = price_tag.get_text(strip=True) if price_tag else "No price"

            message = f"🏠 *New Listing Detected!*\n\n📍 *Address*: {address}\n💷 *Price*: {price}\n🔗 [View Listing]({full_link})"
            send_telegram(message)

        print(f"✅ Found {new_count} new listings.")
    except Exception as e:
        print("💥 Error during scraping:", e)
        send_telegram(f"💥 Scraping error:\n{e}")

# === Bot Runner ===
def start_bot():
    print("🔥 start_bot() has started running")
    send_telegram("🤖 Clarion bot is now running...")
    while True:
        scrape_listings()
        time.sleep(60)

# === Self-Ping for Render Uptime ===
def self_ping():
    while True:
        try:
            requests.get(SELF_URL, timeout=5)
        except Exception as e:
            print("⚠️ Self-ping failed:", e)
        time.sleep(300)

# === Flask Route ===
@app.route("/")
def home():
    return "✅ Clarion bot is alive and scanning!"

# === Main ===
if __name__ == "__main__":
    threading.Thread(target=start_bot).start()
    threading.Thread(target=self_ping).start()
    app.run(host="0.0.0.0", port=10000)
