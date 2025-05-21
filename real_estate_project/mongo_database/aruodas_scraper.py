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
from properties_mongo_db import save_property

# # === SETUP DRIVER ===
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

#Path to your chromedriver.exe
service = Service("C:/Users/dmste/Downloads/chromedriver-win64 (1)/chromedriver-win64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)

base_url = "https://www.aruodas.lt/butai/"
page = 1

while True:
    print(f"\nScraping page {page}...")

    try:
        driver.get(f"{base_url}puslapis/{page}/")

        # Accept cookie popup if present
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            ).click()
            print("Cookie popup accepted.")
        except:
            print("No cookie popup or already accepted.")

        # Wait for listings to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "list-row-v2.object-row.selflat.advert"))
        )
        print("Listings loaded.")
    except TimeoutException:
        print("Page failed to load or no listings found.")
        break

    #Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    ads = soup.find_all("div", class_="advert-flex")

    if not ads:
        print("No listings found on this page. Ending scrape.")
        break

    print(f"Found {len(ads)} listings.\n")

    for ad in ads:
        a_tag = ad.find("a", href=True)
        img_tag = a_tag.find("img") if a_tag else None

        if img_tag and img_tag.has_attr("title"):
            title_attr = img_tag["title"]
            location_info = title_attr.split(" | ")[0]
            parts = location_info.split(", ")

            city = parts[0] if len(parts) > 0 else "N/A"
            district = parts[1] if len(parts) > 1 else "N/A"
            street = parts[2] if len(parts) > 2 else "N/A"
        else:
            city = district = street = rooms = "N/A"

        price_tag = ad.find("span", class_="list-item-price-v2")
        price_per_m2_tag = ad.find("span", class_="price-pm-v2")
        number_of_rooms = ad.find("div", class_="list-RoomNum-v2 list-detail-v2")
        size = ad.find("div", class_="list-AreaOverall-v2 list-detail-v2")
        url_tag = ad.find("a", href=True)

        if not all([price_tag, price_per_m2_tag, number_of_rooms]):
            print("Skipping incomplete listing")
            continue

        title = f"{city}  {district}  {street}"
        raw_price = price_tag.text.strip() if price_tag else None
        match_price = re.findall(r"\d+", raw_price.replace(" ", ""))
        price = float("".join(match_price)) if match_price else "N/A"
        raw_price_per_m2 = price_per_m2_tag.text.strip() if price_per_m2_tag else None
        match_price_mq = re.findall(r"\d+", raw_price_per_m2.replace(" ", ""))  # Remove spaces first
        price_per_m2 = int("".join(match_price_mq)) if match_price_mq else "N/A"
        number_of_rooms = number_of_rooms.text.strip() if number_of_rooms else None
        size = size.text.strip() if size else "N/A"
        url = url_tag["href"] if url_tag and url_tag.has_attr("href") else "N/A"



        property_data = {
            "city": city,
            "district": district,
            "street": street,
            "price": price,
            "size_m2": float(size),
            "price_per_m2": int(price_per_m2),
            "number_of_rooms": int(number_of_rooms),
            "url": url
        }
        save_property(property_data)
        print(f"Saved: {city}, {district} - {price} EUR")
    page += 1

driver.quit()