from playwright.sync_api import sync_playwright
import logging 
import subprocess
import sys 
from pathlib import Path


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
        
        # Add wait for element to be visible
        page.wait_for_selector('input[type="checkbox"]')
        
        checkbox = page.get_by_label("I understand the prohibitions on obtaining and use of financial disclosure reports.")
        checkbox.check()
        
        print("Accepted Senate disclosure agreement")
        logger.info("Accepted Senate disclosure agreement")
        sys.stdout.flush()
        
        # Add explicit wait after checking
        page.wait_for_timeout(1000)  # Wait 1 second
        
        # Keep browser open after success
        input("Press Enter to close browser...")
        
    except Exception as e:
        logger.error(f"Failed to accept Senate disclosure agreement: {e}")
        sys.stdout.flush()
        raise  # Re-raise exception to see full error
    finally:
        browser.close()
        p.stop()
        
    # # Set filters
    # page.get_by_label("Senator", exact=True).check()
    # page.get_by_label("Annual", exact=True).check()
    # page.locator('#fromDate').fill('01/01/2024')
    
    # # Search
    # page.get_by_role('button', name='Search Reports').click()
    # logger.info("Search complete")
    
    # input("Press Enter to close browser...")
    
    # browser.close()
    # p.stop()    
    # # Set filters using labels instead of IDs
    # page.get_by_label("Senator", exact=True).check()
    # page.get_by_label("Annual", exact=True).check()
    # page.locator('#fromDate').fill('01/01/2024')
    # logger.info("Set search filters")
    
    # # Search
    # page.get_by_role('button', name='Search Reports').click()
    # logger.info("Clicked search")
    
    # # Keep browser open
    # input("Press Enter to close browser...")
    
    # browser.close()
    # p.stop()

def run():
    ensure_playwright()
    init_senate_search()

if __name__ == "__main__":
    run()
