import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("OLXScraper")

# List of URLs for transport-related categories
transport_urls = [
    "https://www.olx.uz/transport/legkoye-avtomobili/currency-UZS/",
    "https://www.olx.uz/transport/mototsikly/",
    "https://www.olx.uz/transport/gruzoviki/",
    "https://www.olx.uz/transport/spetstehnika/",
    "https://www.olx.uz/transport/pritsepy/",
    "https://www.olx.uz/transport/vodnyy-transport/",
]


# Retrieve and process webpage content
def fetch_content(web_address):
    log.info(f"Attempting to access {web_address}")
    try:
        response = requests.get(web_address, timeout=10)
        if response.status_code != 200:
            log.error(f"Access failed for {web_address} with status {response.status_code}")
            return None
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as error:
        log.error(f"Failed to retrieve {web_address}: {error}")
        return None


# Collect ad details from the webpage
def gather_ad_details(soup, section_name):
    if not soup:
        return []
    ad_elements = soup.select('div[data-cy="l-card"]')
    collected_data = []

    for ad in ad_elements:
        try:
            title = ad.select_one('h4').text.strip() if ad.select_one('h4') else "N/A"
            price = ad.select_one('p[data-testid="ad-price"]').text.strip() if ad.select_one(
                'p[data-testid="ad-price"]') else "N/A"
            link = ad.select_one('a')['href'] if ad.select_one('a') and 'href' in ad.select_one('a').attrs else "N/A"
            if link != "N/A" and not link.startswith('http'):
                link = f"https://www.olx.uz{link}"
            location_date = ad.select_one('p[data-testid="location-date"]').text.strip() if ad.select_one(
                'p[data-testid="location-date"]') else "N/A"

            collected_data.append({
                'Item': title,
                'Cost': price,
                'Link': link,
                'Place and Time': location_date,
            })
        except Exception as error:
            log.error(f"Issue with ad in {section_name}: {error}")
            continue

    log.info(f"Collected {len(collected_data)} items from {section_name}")
    return collected_data


# Store data in a CSV file with a simpler name
def store_results(data, section):
    if not data:
        log.warning(f"No items to store for {section}")
        return
    try:
        filename = "transport_data.csv"
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
        log.info(f"Saved data to {filename}")
    except Exception as error:
        log.error(f"Could not save data for {section}: {error}")


# Extract category name from URL
def get_section_name(web_link):
    return web_link.split('/')[-2] if web_link.endswith('/') else web_link.split('/')[-1]


# Process each category
def process_category(web_link):
    page_content = fetch_content(web_link)
    if page_content:
        section = get_section_name(web_link)
        log.info(f"Processing section: {section}")
        ad_data = gather_ad_details(page_content, section)
        store_results(ad_data, section)
        sleep(3)


# Main execution flow
def run_scraper():
    log.info("Beginning OLX.uz data collection...")
    for url in transport_urls:
        process_category(url)
    log.info("Data collection finished.")


if __name__ == "__main__":
    run_scraper()