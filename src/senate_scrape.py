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
            final_df = pd.concat(all_data, ignore_index=True)
            print(f"Total rows collected: {len(final_df)}")
            print(final_df.head())
            timestamp = time.strftime("%Y-%m-%d")
            final_df.to_csv(f"senate_disclosures_unenriched_{timestamp}.csv")
            logging.info(f"Data saved to senate_disclosures_unenriched_{timestamp}.csv")
    
                # # Extract links from HTML using BeautifulSoup
                # soup = BeautifulSoup(table_html, 'html.parser')
                # table = soup.find('table', {'id': 'filedReports'})
                # links = []
                # for row in table.find_all('tr')[1:]:  # Skip header row
                #     link_cell = row.find('a')
                #     if link_cell and 'href' in link_cell.attrs:
                #         links.append('https://efdsearch.senate.gov' + link_cell['href'])
                #     else:
                #         links.append('')
                
                # # Add links column to dataframe        
                # df['Link'] = links
                # print(df.head())
                # data = df.values.tolist()
                # report_link = ''
                # filename = ''

                #     for index, cell in enumerate(cells):
                #         # If this is the Report Type column, extract the link
                #         if index == 3:  # Assuming Report Type is the 4th column (0-indexed)
                #             link_element = cell.query_selector('a')
            #                 if link_element:
            #                     report_href = link_element.get_attribute('href')
            #                     report_link = base_url + report_href
            #                     cell_text = link_element.inner_text().strip()
            #                 else:
            #                     cell_text = cell.inner_text().strip()
            #             else:
            #                 cell_text = cell.inner_text().strip()
            #                 # Remove '(Senator)' from names if present
            #                 if index in [0, 1]:  # First Name and Last Name columns
            #                     cell_text = cell_text.replace('(Senator)', '').strip()
            #             data.append(cell_text)

            #         # Combine First Name and Last Name into one column
            #         full_name = f"{data[1]}, {data[0]}"  # "LAST NAME, First Name"
            #         # Remove the original First Name and Last Name columns
            #         data = data[2:]  # Remove first two elements
            #         # Insert the full_name at the beginning
            #         data.insert(0, full_name)
            #         # Append the full report link
            #         data.append(report_link)
            #         # Add 'Annoying' and 'Standard' columns based on URL
            #         annoying = 'TRUE' if 'paper' in report_link.lower() else 'FALSE'
            #         standard = 'TRUE' if 'annual' in report_link.lower() else 'FALSE'
            #         data.append(annoying)
            #         data.append(standard)

            #         # Handle report download
            #         if report_link:
            #             # Click on the report link
            #             row.click()
            #             page.wait_for_load_state('networkidle')
            #             time.sleep(2)  # Wait for any dynamic content to load

            #             # Check for 'Printer-Friendly' button
            #             printer_friendly_buttons = page.query_selector_all('a.btn.btn-primary.btn-sm.ml-1:has-text("Printer-Friendly")')
            #             if printer_friendly_buttons:
            #                 logger.info("Printer-Friendly button found. Clicking to download printer-friendly version.")
            #                 printer_friendly_button = printer_friendly_buttons[0]
            #                 printer_friendly_button.click()
            #                 time.sleep(5)  # Wait for the new tab to open and load

            #                 # Get all pages (tabs) in the browser
            #                 pages = context.pages
            #                 if len(pages) > 1:
            #                     # The new tab is the last in the list
            #                     printer_friendly_page = pages[-1]
            #                     printer_friendly_page.wait_for_load_state('networkidle')

            #                     # Generate a unique filename based on report details
            #                     safe_name = full_name.replace(',', '').replace(' ', '_')
            #                     pf_filename = f"{safe_name}_printer_friendly"

            #                     # Download the Printer-Friendly page as PDF
            #                     pdf_path = download_page_as_pdf(printer_friendly_page, pf_filename)
            #                     filename = pdf_path if pdf_path else ''

            #                     # Close the Printer-Friendly tab
            #                     printer_friendly_page.close()
            #                 else:
            #                     logger.error("Printer-Friendly tab did not open as expected.")
            #             else:
            #                 logger.info("No Printer-Friendly button found. Downloading regular report.")
            #                 # Generate a unique filename based on report details
            #                 safe_name = full_name.replace(',', '').replace(' ', '_')
            #                 regular_filename = f"{safe_name}_report"

            #                 # Download the current report page as PDF
            #                 pdf_path = download_page_as_pdf(page, regular_filename)
            #                 filename = pdf_path if pdf_path else ''

            #             # Navigate back to the search results
            #             page.go_back()
            #             page.wait_for_load_state('networkidle')
            #             time.sleep(2)  # Allow time for the page to load
            #         else:
            #             logger.warning("No report link found for this row.")

            #         # Append the filename to the data
            #         data.append(filename if filename else '')

            #         all_data.append(data)
            #         logger.info(f"Processed report for {full_name}")
            #         sys.stdout.flush()

            #     print(f"Scraped page {current_page}")
            #     logger.info(f"Scraped page {current_page}")
            #     sys.stdout.flush()

            #     # Check if there is a next page
            #     next_button = page.query_selector('a.paginate_button.next')
            #     if next_button and 'disabled' not in next_button.get_attribute('class'):
            #         next_button.click()
            #         page.wait_for_load_state('networkidle')
            #         current_page += 1
            #         time.sleep(2)  # Additional wait to ensure page has loaded
            #     else:
            #         break

            # # Define columns including the new 'Filename' column
            # columns = ['Name', 'Office (Filer Type)', 'Report Type', 'Date Received/Filed', 'Report Link', 'Annoying', 'Standard', 'Filename']
            # df = pd.DataFrame(all_data, columns=columns)

            # # Save to CSV
            # df.to_csv('senate_disclosure_reports.csv', index=False)
            # logger.info("Data saved to senate_disclosure_reports.csv")
            # print("Data saved to senate_disclosure_reports.csv")
            # sys.stdout.flush()

            # # Close the browser
            # browser.close()

            # return df

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            browser.close()
            raise

# def download_page_as_pdf(page: Page, filename: str, download_dir: str = 'senate_reports') -> Optional[str]:
#     """
#     Download the current page as a PDF.

#     Args:
#         page (Page): Playwright page object.
#         filename (str): Desired filename for the PDF.
#         download_dir (str): Directory to save the downloaded PDFs.

#     Returns:
#         str: Path to the downloaded PDF, or None if failed.
#     """
#     try:
#         os.makedirs(download_dir, exist_ok=True)
#         file_path = Path(download_dir) / f"{filename}.pdf"
#         # Ensure filename is unique
#         if file_path.exists():
#             timestamp = int(time.time())
#             file_path = Path(download_dir) / f"{filename}_{timestamp}.pdf"
#         page.pdf(path=str(file_path))
#         logger.info(f"Downloaded PDF: {file_path}")
#         return str(file_path)
#     except Exception as e:
#         logger.error(f"Error downloading PDF for {filename}: {e}")
#         return None




def run():
    ensure_playwright()
    init_senate_search()


if __name__ == "__main__":
    run()
