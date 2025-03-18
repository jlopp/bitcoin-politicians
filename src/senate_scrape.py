import os
import sys
import time
import json
import logging
import requests
import pandas as pd
from pathlib import Path
from playwright.sync_api import sync_playwright, Page
from typing import Optional
import subprocess
from bs4 import BeautifulSoup 


# Configure logging to output to both console and logs.txt
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)  # Console handler set to INFO

file_handler = logging.FileHandler('logs.txt')
file_handler.setLevel(logging.DEBUG)  # File handler set to DEBUG

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def ensure_playwright():
    """Install Playwright Chromium browser if not installed"""
    browser_path = Path.home() / '.cache' / 'ms-playwright'
    if not any(browser_path.glob('chromium-*')):  # Check for any chromium version
        logger.info("Installing Playwright Chromium browser if not installed...")
        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], check=True)
        logger.info("Playwright Chromium installed successfully")


def init_senate_search():
    """Initialize Senate financial disclosure search, set filters, scrape data, download reports, and append filenames"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to the Senate financial disclosure search page
            page.goto('https://efdsearch.senate.gov/search/')
            page.wait_for_selector('#agree_statement', timeout=15000)

            # Accept terms
            checkbox = page.locator('#agree_statement')
            checkbox.check()
            logger.info("Accepted Senate disclosure agreement")
            sys.stdout.flush()

            # Set filters using precise selectors
            time.sleep(10)
            print("Sleeping....")

            page.locator('input[name="filer_type"][value="1"]').check()  # Check 'Senator'
            page.locator('input[name="report_type"][value="7"]').check()  # Check 'Annual'
            page.locator('#fromDate').fill('01/01/2024')  # Set 'From' date
            logger.info("Set search filters")
            print("Set search filters")
            sys.stdout.flush()

            # Click search button
            search_button = page.get_by_role('button', name='Search Reports')
            search_button.click()
            logger.info("Clicked search")
            print("Clicked search")
            sys.stdout.flush()

            print("Wait for search results to load")
            time.sleep(5)

            print("Scrape data from the table, handling pagination")
            all_data = []
            current_page = 1
            base_url = 'https://efdsearch.senate.gov'

            while True:
                print(f"Processing page {current_page}")
                print("Wait for the table body to load")
                time.sleep(2.5)

                print("Scraping")
                # Get HTML content of the table and parse with pandas
                table_html = page.content()
                # Parse table with pandas
                dfs = pd.read_html(table_html)
                df = dfs[0]  # Get first table
                
                # Use BeautifulSoup to get links from Report Type column
                soup = BeautifulSoup(table_html, 'html.parser')
                links = [base_url + a['href'] if a else '' for a in soup.select('table#filedReports a')]
                df['Report URL'] = links
                
                # Append the current page's data
                all_data.append(df)
                print(f"Added {len(df)} rows from page {current_page}")
                
                # Check for next page button
                next_page_button = page.query_selector(f'a[data-dt-idx="{current_page + 1}"]')
                if not next_page_button:
                    print("No more pages to process")
                    break
                    
                # Click next page and wait
                next_page_button.click()
                current_page += 1
                time.sleep(2)  # Wait for new page to load
            
            # Combine all dataframes
            final_df = pd.concat(all_data, ignore_index=False)
            print(f"Total rows collected: {len(final_df)}")
            print(final_df.head())
            final_df.to_csv(f"senate_disclosures.csv")
            logging.info(f"Data saved to senate_disclosures.csv")
    

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            browser.close()
            raise

def download_page_as_pdf(page: Page, filename: str, download_dir: str = 'senate_reports') -> Optional[str]:
    """
    Download the current page as a PDF.

    Args:
        page (Page): Playwright page object.
        filename (str): Desired filename for the PDF.
        download_dir (str): Directory to save the downloaded PDFs.

    Returns:
        str: Path to the downloaded PDF, or None if failed.
    """
    try:
        os.makedirs(download_dir, exist_ok=True)
        file_path = Path(download_dir) / f"{filename}.pdf"
        # Ensure filename is unique
        if file_path.exists():
            timestamp = int(time.time())
            file_path = Path(download_dir) / f"{filename}_{timestamp}.pdf"
        page.pdf(path=str(file_path))
        logger.info(f"Downloaded PDF: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"Error downloading PDF for {filename}: {e}")
        return None




def run():
    ensure_playwright()
    init_senate_search()


if __name__ == "__main__":
    run()
