import os
import sys
import time
import json
import base64
import cv2
import logging
import pytesseract
import tempfile
import requests
import pandas as pd
from pathlib import Path
from pdf2image import convert_from_path
import openai
from math import ceil
import PyPDF2
from PIL import Image
from config import CRYPTO_ASSETS
import numpy as np
from playwright.sync_api import sync_playwright
from typing import Dict, List, Optional, Union
import subprocess

# Try to find tesseract in common installation paths
tesseract_paths = [
    "/usr/local/bin/tesseract",
    "/usr/bin/tesseract",
    "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",  # Windows path
    "/opt/homebrew/bin/tesseract"  # Mac Homebrew path
]

tesseract_found = False
for path in tesseract_paths:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        tesseract_found = True
        break

if not tesseract_found:
    raise RuntimeError("Tesseract is not installed or not found in common paths. Please install Tesseract and ensure it's in your PATH.")

# Configure OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

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

def download_report(report_url: str, download_dir: str = 'senate_reports') -> Optional[str]:
    """
    Download the report PDF from the given URL.

    Args:
        report_url (str): URL of the report to download.
        download_dir (str): Directory to save the downloaded reports.

    Returns:
        str: Filename of the downloaded report, or None if failed.
    """
    try:
        os.makedirs(download_dir, exist_ok=True)
        response = requests.get(report_url, timeout=30)
        if response.status_code == 200:
            # Extract filename from URL
            filename = report_url.split('/')[-1]
            # Ensure filename is unique by appending timestamp if necessary
            file_path = Path(download_dir) / filename
            if file_path.exists():
                timestamp = int(time.time())
                filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
                file_path = Path(download_dir) / filename
            with open(file_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Downloaded report: {file_path}")
            return str(file_path)
        else:
            logger.error(f"Failed to download report from {report_url}. Status code: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error downloading report from {report_url}: {e}")
        return None

def init_senate_search():
    """Initialize Senate financial disclosure search, set filters, scrape data, download reports, and append filenames"""
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    try:
        # Navigate to the Senate financial disclosure search page
        page.goto('https://efdsearch.senate.gov/search/')
        page.wait_for_selector('#agree_statement', timeout=10000)

        # Accept terms
        checkbox = page.locator('#agree_statement')
        checkbox.check()
        time.sleep(5)  # Allow time for any page updates

        print("Accepted Senate disclosure agreement")
        logger.info("Accepted Senate disclosure agreement")
        sys.stdout.flush()

        # Click the 'Search Reports' button to proceed
        search_reports_button = page.locator('button:has-text("Search Reports")')
        search_reports_button.click()

        # Wait for search form to load
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
            page.wait_for_selector('#filedReports tbody tr', timeout=10000)

            # Extract table rows
            rows = page.query_selector_all('#filedReports tbody tr')
            for row in rows:
                cells = row.query_selector_all('td')
                data = []
                report_link = ''
                filename = ''

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

                # Download the report and get the filename
                if report_link:
                    filename = download_report(report_link)
                else:
                    logger.warning("No report link found for this row.")
                
                # Append the filename to the data
                data.append(filename if filename else '')

                all_data.append(data)
                logger.info(f"Processed report: {report_link}")
                sys.stdout.flush()

            print(f"Scraped page {current_page}")
            logger.info(f"Scraped page {current_page}")
            sys.stdout.flush()

            # Check if there is a next page
            next_button = page.query_selector('a.paginate_button.next')
            if next_button and 'disabled' not in next_button.get_attribute('class'):
                next_button.click()
                current_page += 1
                # Wait for the next page to load
                page.wait_for_selector('#filedReports_processing', state='hidden', timeout=10000)
                time.sleep(2)  # Additional wait to ensure page has loaded
            else:
                break

        # Define columns including the new 'Filename' column
        columns = ['Name', 'Office (Filer Type)', 'Report Type', 'Date Received/Filed', 'Report Link', 'Annoying', 'Standard', 'Filename']
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
        logger.error(f"An error occurred: {e}")
        raise
    finally:
        browser.close()
        p.stop()

def run():
    ensure_playwright()
    init_senate_search()

if __name__ == "__main__":
    run()
