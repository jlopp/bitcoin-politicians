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


def ensure_playwright():
    """Install playwright chromium if not already installed"""
    browser_path = Path.home() / '.cache' / 'ms-playwright' / 'chromium-' 
    
    if not any(browser_path.parent.glob('chromium-*')):  # Check for any chromium version
        logger.info("Installing Playwright Chromium browser if not installed...")
        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], check=True)
        logger.info("Playwright Chromium installed successfully")

from playwright.sync_api import sync_playwright
import logging 
import subprocess
import sys 
from pathlib import Path
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_playwright():
    """Install Playwright Chromium browser if not installed"""
    browser_path = Path.home() / '.cache' / 'ms-playwright' / 'chromium-' 
    if not any(browser_path.parent.glob('chromium-*')):  # Check for any chromium version
        logger.info("Installing Playwright Chromium browser if not installed...")
        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], check=True)
        logger.info("Playwright Chromium installed successfully")

from playwright.sync_api import sync_playwright
import logging 
import subprocess
import sys 
from pathlib import Path
import pandas as pd
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_playwright():
    """Install Playwright Chromium browser if not installed"""
    browser_path = Path.home() / '.cache' / 'ms-playwright' / 'chromium-' 
    if not any(browser_path.parent.glob('chromium-*')):  # Check for any chromium version
        logger.info("Installing Playwright Chromium browser if not installed...")
        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], check=True)
        logger.info("Playwright Chromium installed successfully")

def init_senate_search():
    """Initialize Senate financial disclosure search, set filters, and scrape data"""
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    try:
        # Accept terms
        page.goto('https://efdsearch.senate.gov/search/')
        page.wait_for_selector('input[type="checkbox"]')

        checkbox = page.get_by_label("I understand the prohibitions on obtaining and use of financial disclosure reports.", exact=True)
        checkbox.check()
        time.sleep(1)  # Allow time for any page updates

        print("Accepted Senate disclosure agreement")
        logger.info("Accepted Senate disclosure agreement")
        sys.stdout.flush()

        # Wait for the search form to be visible on the new page
        page.wait_for_selector('#searchForm')

        # Set filters using precise selectors
        page.locator('input[name="filer_type"][value="1"]').check()  # Check 'Senator'
        page.locator('input[name="report_type"][value="7"]').check()  # Check 'Annual'
        page.locator('#fromDate').fill('01/01/2024')  # Set 'From' date
        logger.info("Set search filters")
        print("Set search filters")
        sys.stdout.flush()

        # Click search button
        page.get_by_role('button', name='Search Reports').click()
        logger.info("Clicked search")
        print("Clicked search")
        sys.stdout.flush()

        # Wait for search results to load
        page.wait_for_selector('#filedReports')

        # Scrape data from the table, handling pagination
        all_data = []
        current_page = 1
        base_url = 'https://efdsearch.senate.gov'

        while True:
            # Wait for the table body to load
            page.wait_for_selector('#filedReports tbody tr')

            # Extract table rows
            rows = page.query_selector_all('#filedReports tbody tr')
            for row in rows:
                cells = row.query_selector_all('td')
                data = []
                report_link = ''
                for index, cell in enumerate(cells):
                    # If this is the Report Type column, extract the link
                    if index == 3:  # Assuming Report Type is the 4th column (0-indexed)
                        link_element = cell.query_selector('a')
                        if link_element:
                            relative_link = link_element.get_attribute('href')
                            report_link = base_url + relative_link
                            # Get the text inside the link (Report Type)
                            cell_text = link_element.inner_text().strip()
                        else:
                            cell_text = cell.inner_text().strip()
                    else:
                        cell_text = cell.inner_text().strip()
                        # Remove '(Senator)' from names if present
                        if index in [0, 1]:  # First Name and Last Name columns
                            cell_text = cell_text.replace('(Senator)', '').strip()
                    data.append(cell_text)
                # Combine First Name and Last Name into one column
                full_name = f"{data[1]}, {data[0]}"  # "LAST NAME, First Name"
                # Remove the original First Name and Last Name columns
                data = data[2:]  # Remove first two elements
                # Insert the full_name at the beginning
                data.insert(0, full_name)
                # Append the full report link
                data.append(report_link)
                # Add 'Annoying' and 'Standard' columns based on URL
                data.append('TRUE' if 'paper' in report_link.lower() else 'FALSE')  # Annoying
                data.append('TRUE' if 'annual' in report_link.lower() else 'FALSE')  # Standard
                all_data.append(data)

            print(f"Scraped page {current_page}")
            logger.info(f"Scraped page {current_page}")
            sys.stdout.flush()

            # Check if there is a next page
            next_button = page.query_selector('a.paginate_button.next')
            if next_button and 'disabled' not in next_button.get_attribute('class'):
                next_button.click()
                current_page += 1
                # Wait for the next page to load
                page.wait_for_selector('#filedReports_processing', state='hidden')
            else:
                break

        # Convert data to DataFrame
        columns = ['Name', 'Office (Filer Type)', 'Report Type', 'Date Received/Filed', 'Report Link', 'Annoying', 'Standard']
        df = pd.DataFrame(all_data, columns=columns)

        # Save to CSV
        df.to_csv('senate_disclosure_reports.csv', index=False)
        logger.info("Data saved to senate_disclosure_reports.csv")
        print("Data saved to senate_disclosure_reports.csv")
        sys.stdout.flush()

        # Keep browser open after success
        input("Press Enter to close browser...")
        return df

    except Exception as e:
        logger.error(f"Failed to perform search: {e}")
        sys.stdout.flush()
        raise  # Re-raise exception to see full error
    finally:
        browser.close()
        p.stop()

def run():
    ensure_playwright()
    init_senate_search()

if __name__ == "__main__":
    run()
        

def run():
    ensure_playwright()
    init_senate_search()

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
