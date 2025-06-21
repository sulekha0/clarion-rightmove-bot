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

            # Save + print HTML (first 1000 chars) to debug if listings exist
            html = soup.prettify()
            with open("live_output.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("🔍 First 1000 chars of live HTML:\n" + html[:1000])

        listings = soup.find_all("div", class_="PropertyCard_propertyCardContainer__VSRSA")
        print(f"🧾 Total listings found using selector: {len(listings)}")
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
