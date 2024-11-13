from playwright.sync_api import sync_playwright
from pathlib import Path
from typing import Dict, List, Optional, Union

import logging 
import subprocess
import sys 
import time
import pandas as pd



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)



def init_house_search():
    """Retrieve all House financial disclosure filings for the most recent year."""
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    try:
        print(f"Going to page...")
        # Go to the House Financial Disclosure website
        page.goto('https://disclosures-clerk.house.gov/FinancialDisclosure')
        time.sleep(2)
        # Click the 'Search' link
        print("Click link...")
        page.click('a[href="#Search"][data-custom-nav="sidenav"][data-view="ViewSearch"][aria-controls="Search"][data-toggle="pill"]')
        print("Link clicked...")
        time.sleep(2)
        # Wait for the filing year dropdown to be visible
        page.wait_for_selector('#FilingYear')
        
        # Get all options and find most recent year
        options = page.evaluate('Array.from(document.querySelectorAll("#FilingYear option")).map(o => o.value)')
        valid_years = [int(y) for y in options if y.isdigit()]
        most_recent_year = str(max(valid_years))
        
        # Select the most recent year
        page.select_option('#FilingYear', most_recent_year)
        print(f"Selected filing year: {most_recent_year}")
        time.sleep(1)  # Brief pause to let the selection take effect

        # Click the search button
        search_button = page.get_by_role('button', name='Search')
        search_button.click()
        print("Clicked search button")
        time.sleep(2)  # Allow time for search results to load

        # Now, we will collect data from all pages
        all_data = []

        base_url = 'https://disclosures-clerk.house.gov/'

        page_number = 1
        while True:
            print(f"Processing page {page_number}")
            time.sleep(3)
            # Wait for table to be loaded
            
            # Get table HTML and read with pandas
            print("Getting table")
            # Get table data
            df = pd.read_html(page.content())[0]
            
            # Extract links from the Report Type column
            links = page.query_selector_all('table tbody tr td a')
            report_urls = []
            for link in links:
                href = link.get_attribute('href')
                if href:
                    full_url = base_url + href
                    report_urls.append(full_url)
                else:
                    report_urls.append('')
                    
            # Add Report URL column
            df['Report URL'] = report_urls
            
            df.to_csv('awmanali.csv')
            print(df.head())
            print(df.columns)
            print("Got table")
            
        #     # Extract links from table
            
        #     # Check for next page
        #     next_button = page.query_selector('a#DataTables_Table_0_next')
        #     if next_button:
        #         class_attr = next_button.get_attribute('class')
        #         if 'disabled' in class_attr:
        #             break
        #         else:
        #             next_button.click()
        #             time.sleep(2)
        #             page_number += 1
        #     else:
        #         break
        # # Create DataFrame
        # df = pd.DataFrame(all_data)
        # return df

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close browser
        browser.close()
        p.stop()        
        return page


def run():
    init_house_search()


if __name__ == "__main__":
    run()

    


# def categorize_link(url: str) -> str:
#     """Return 'table' or 'manual' based on PDF structure"""
#     # Logic to determine if PDF has HTML tables or needs manual extraction
#     return None

# def extract_crypto_from_manual_upload(url: str) -> Dict:
#     """Extract crypto holdings from PDF with tables"""
#     # Use OpenAI to parse table data
#     return None 

# def extract_crypto_html(url: str) -> Dict:
#     """Extract crypto holdings from handwritten/letter PDFs"""
#     # Use OpenAI for more complex extraction
#     return None


#     ### handle html (download)
#     ### handle pages (download)

# def run():
#     ensure_playwright()
#     init_senate_search()

# if __name__ == "__main__":
#     run()
