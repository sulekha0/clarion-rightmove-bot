def get_new_listings():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(URL, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        cards = soup.select("div[data-testid='propertyCard']")
        print(f"🔍 Found {len(cards)} property cards")
        results = []

        for card in cards:
            try:
                link = card.select_one("a[data-testid='property-title-link']")
                title = link.get("title", "No title")  # fallback title if missing
                location = card.select_one("address")
                price = card.select_one("div[data-testid='property-price']")

                if not all([link, location, price]):
                    continue

                href = "https://www.rightmove.co.uk" + link["href"]
                if href in seen_links:
                    continue

                seen_links.add(href)

                message = (
                    f"🏡 <b>{title.strip()}</b>\n"
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
