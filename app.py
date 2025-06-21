import time
import requests
import threading
from flask import Flask
from bs4 import BeautifulSoup
from datetime import datetime
import os

# === CONFIGURATION ===
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("CHAT_ID")
RIGHTMOVE_URL = "https://www.rightmove.co.uk/property-to-rent/find/Clarion-Housing-Lettings/UK.html?locationIdentifier=BRANCH%5E58989&propertyStatus=all&includeLetAgreed=true&_includeLetAgreed=on"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

sent_ids = set()
app = Flask(__name__)

# === FUNCTION TO SCRAPE LISTINGS ===
def get_new_listings():
    print(f"🔍 Checking for new listings at {datetime.now().strftime('%H:%M:%S')}...")
    try:
        response = requests.get(RIGHTMOVE_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"💥 Scraping error:\n{e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    cards = soup.select("div[data-testid^='propertyCard']")
    new_listings = []

    for card in cards:
        try:
            link_tag = card.select_one("a[href*='/properties/']")
            if not link_tag:
                continue

            property_id = link_tag['href'].split('/')[2]
            full_url = "https://www.rightmove.co.uk" + link_tag['href']

            if property_id in sent_ids:
                continue

            description_tag = card.select_one("p[data-testid='property-description']")
            price_tag = card.select_one("div.PropertyPrice_price__VL65t")
            address_tag = card.select_one("address")

            description = description_tag.text.strip() if description_tag else "No description"
            price = price_tag.text.strip() if price_tag else "No price"
            address = address_tag.text.strip() if address_tag else "No address"

            message = f"🏡 <b>{address}</b>\n💷 {price}\n📝 {description}\n🔗 {full_url}"
            new_listings.append((property_id, message))
        except Exception as e:
            print(f"⚠️ Failed to parse a card:\n{e}")
            continue

    return new_listings

# === FUNCTION TO SEND TELEGRAM MESSAGE ===
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "H
