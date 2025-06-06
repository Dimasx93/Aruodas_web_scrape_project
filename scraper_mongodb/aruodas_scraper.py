# Final project, Webscraping Aruodas

import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from .properties_mongo_db import save_property


def scrape_aruodas() -> None:
    """
    Scrapes apartment listings from aruodas.lt and stores each listing in MongoDB using `save_property`.

    This function uses Selenium to navigate through the pages of aruodas.lt listings and BeautifulSoup
    to parse the HTML content. Listings are extracted from the DOM and parsed into structured data.
    Listings without critical information (e.g., price, room count) are skipped.

    Extracted data includes:
    - City, district, street
    - Price and price per square meter
    - Apartment size (m²)
    - Number of rooms
    - URL to the listing

    The parsed data is saved using the `save_property` function.
    """
    # === SETUP DRIVER ===
    chrome_options: Options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service: Service = Service("C:/Users/dmste/Downloads/chromedriver-win64 (1)/chromedriver-win64/chromedriver.exe")
    driver: webdriver.Chrome = webdriver.Chrome(service=service, options=chrome_options)

    base_url: str = "https://www.aruodas.lt/butai/"
    page: int = 1

    while True:
        print(f"\nScraping page {page}...")

        try:
            driver.get(f"{base_url}puslapis/{page}/")

            try:
                # Accept cookie consent popup if present
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                ).click()
                print("Cookie popup accepted.")
            except:
                print("No cookie popup or already accepted.")

            # Wait for listing container to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "list-row-v2.object-row.selflat.advert"))
            )
            print("Listings loaded.")

        except TimeoutException:
            print("Page failed to load or no listings found.")
            break

        soup: BeautifulSoup = BeautifulSoup(driver.page_source, "html.parser")
        ads = soup.find_all("div", class_="advert-flex")

        if not ads:
            print("No listings found on this page. Ending scrape.")
            break

        print(f"Found {len(ads)} listings.\n")

        for ad in ads:
            a_tag = ad.find("a", href=True)
            img_tag = a_tag.find("img") if a_tag else None

            if img_tag and img_tag.has_attr("title"):
                title_attr: str = img_tag["title"]
                location_info: str = title_attr.split(" | ")[0]
                parts = location_info.split(", ")

                city: str = parts[0] if len(parts) > 0 else "N/A"
                district: str = parts[1] if len(parts) > 1 else "N/A"
                street: str = parts[2] if len(parts) > 2 else "N/A"
            else:
                city = district = street = "N/A"

            price_tag = ad.find("span", class_="list-item-price-v2")
            price_per_m2_tag = ad.find("span", class_="price-pm-v2")
            number_of_rooms_tag = ad.find("div", class_="list-RoomNum-v2 list-detail-v2")
            size_tag = ad.find("div", class_="list-AreaOverall-v2 list-detail-v2")
            url_tag = ad.find("a", href=True)

            if not all([price_tag, price_per_m2_tag, number_of_rooms_tag]):
                print("Skipping incomplete listing")
                continue

            title: str = f"{city}  {district}  {street}"

            raw_price: str = price_tag.text.strip()
            match_price = re.findall(r"\d+", raw_price.replace(" ", ""))
            price: float = float("".join(match_price)) if match_price else 0.0

            raw_price_per_m2: str = price_per_m2_tag.text.strip()
            match_price_mq = re.findall(r"\d+", raw_price_per_m2.replace(" ", ""))
            price_per_m2: int = int("".join(match_price_mq)) if match_price_mq else 0

            number_of_rooms: int = int(number_of_rooms_tag.text.strip())
            size_m2: float = float(size_tag.text.strip()) if size_tag else 0.0

            url: str = url_tag["href"] if url_tag and url_tag.has_attr("href") else "N/A"

            property_data: dict = {
                "city": city,
                "district": district,
                "street": street,
                "price": price,
                "size_m2": size_m2,
                "price_per_m2": price_per_m2,
                "number_of_rooms": number_of_rooms,
                "url": url
            }

            save_property(property_data)
            print(f"Saved: {city}, {district} - {price} EUR")

        page += 1

    driver.quit()


if __name__ == "__main__":
    scrape_aruodas()