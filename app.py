mport requests
from bs4 import BeautifulSoup

URL = "https://www.rightmove.co.uk/property-to-rent/find/Clarion-Housing-Lettings/UK.html?locationIdentifier=BRANCH%5E58989&propertyStatus=all&includeLetAgreed=true&_includeLetAgreed=on"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-GB,en;q=0.9",
}

try:
    print(f"🌐 Requesting {URL}")
    response = requests.get(URL, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select("div[data-test='propertyCard']")
    print(f"✅ Found {len(cards)} property cards.\n")

    for card in cards:
        link = card.select_one("a[data-test='property-title-link']")
        title = card.select_one("h2[data-test='property-title']")
        location = card.select_one("address")
        price = card.select_one("div[data-test='property-price']")

        if not all([link, title, location, price]):
            print("⚠️ Skipping incomplete card.")
            continue

        href = "https://www.rightmove.co.uk" + link["href"]
        print(f"🏡 {title.get_text(strip=True)}")
        print(f"📍 {location.get_text(strip=True)}")
        print(f"💷 {price.get_text(strip=True)}")
        print(f"🔗 {href}\n")

except Exception as e:
    print("❌ Failed to scrape:", e)
