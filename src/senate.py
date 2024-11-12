from playwright.sync_api import sync_playwright
import logging 
import subprocess
import sys 
from pathlib import Path
import time
from typing import Dict, List, Optional, Union



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

def init_senate_search():
    """Initialize Senate financial disclosure search and set filters"""
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    try:
        # Accept terms
        page.goto('https://efdsearch.senate.gov/search/home/')
        time.sleep(0.5)  
        page.wait_for_selector('input[type="checkbox"]')
        checkbox = page.get_by_label("I understand the prohibitions on obtaining and use of financial disclosure reports.")
        with page.expect_navigation():
            checkbox.check()
        logger.info("Accepted Senate disclosure agreement")
        sys.stdout.flush()
        time.sleep(0.5)  # Wait for navigation to complete
        
        # Set filters
        page.wait_for_selector('text=Search Reports')
        time.sleep(0.25)  # Brief pause before setting filters
        page.get_by_label("Senator", exact=True).check()
        time.sleep(0.15)  
        page.get_by_label("Annual", exact=True).check()
        time.sleep(0.15)
        page.locator('#fromDate').fill('01/01/2024')
        logger.info("Set search filters")
        print("Set search filters")
        sys.stdout.flush()
        time.sleep(0.25) 
        
        # Click search button
        page.get_by_role('button', name='Search Reports').click()
        logger.info("Clicked search")
        print("Clicked search")
        sys.stdout.flush()
        time.sleep(0.5) 
        
        # Wait for tables
        page.wait_for_selector('.dataTables_wrapper')  # Adjust the selector based on actual results element
        
        # Keep browser open after success
        input("Press Enter to close browser...")
        
    except Exception as e:
        logger.error(f"Failed to perform search: {e}")
        sys.stdout.flush()
        raise  # Re-raise exception to see full error
    finally:
        browser.close()
        p.stop()

    ### get all links


def get_senate_links(page) -> List[str]:
    """Get all PDF links from Senate disclosure search results"""
    links = []
    # Get total pages (look for pagination)
    # For each page:
        # Get links from current page
        # Click next page if exists
    return links


def categorize_link(url: str) -> str:
    """Return 'table' or 'manual' based on PDF structure"""
    # Logic to determine if PDF has HTML tables or needs manual extraction
    return None

def extract_crypto_from_manual_upload(url: str) -> Dict:
    """Extract crypto holdings from PDF with tables"""
    # Use OpenAI to parse table data
    return None 

def extract_crypto_html(url: str) -> Dict:
    """Extract crypto holdings from handwritten/letter PDFs"""
    # Use OpenAI for more complex extraction
    return None


    ### handle html (download)
    ### handle pages (download)

def run():
    ensure_playwright()
    init_senate_search()

if __name__ == "__main__":
    run()
