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



def get_all_house_disclosures():
    """Retrieve all House financial disclosure filings for the most recent year."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            print(f"Going to page...")
            logger.info("Navigating to House Financial Disclosure website.")
            # Go to the House Financial Disclosure website
            page.goto('https://disclosures-clerk.house.gov/FinancialDisclosure')
            time.sleep(4)  # Wait for the page to load

            # Click the 'Search' link
            print("Clicking search link...")
            logger.info("Clicking the 'Search' link.")
            page.click('a[href="#Search"][data-custom-nav="sidenav"][data-view="ViewSearch"]')
            print("Search link clicked...")
            logger.info("Search link clicked.")
            time.sleep(4)  # Wait for the search form to render

            # Get all options and find most recent year
            print("Retrieving filing years...")
            logger.info("Retrieving filing years from the dropdown.")
            options = page.evaluate('Array.from(document.querySelectorAll("#FilingYear option")).map(o => o.value)')
            valid_years = [int(y) for y in options if y.isdigit()]
            most_recent_year = str(max(valid_years))
            print(f"Most recent year found: {most_recent_year}")
            logger.info(f"Most recent year selected: {most_recent_year}")

            # Select the most recent year
            page.select_option('#FilingYear', most_recent_year)
            print(f"Selected filing year: {most_recent_year}")
            logger.info(f"Selected filing year: {most_recent_year}")
            time.sleep(2)  # Brief pause to let the selection take effect

            # Click the search button
            search_button = page.get_by_role('button', name='Search')
            search_button.click()
            print("Clicked search button")
            logger.info("Clicked search button.")
            time.sleep(4)  # Allow time for search results to load

            # Initialize an empty DataFrame to collect all data
            all_data = pd.DataFrame()
            base_url = 'https://disclosures-clerk.house.gov'

            page_number = 1
            while True:
                print(f"Processing page {page_number}")
                logger.info(f"Processing page {page_number}")
                time.sleep(5)  # Wait for the page to load

                # Get table data
                print("Getting table data...")
                logger.info("Extracting table data.")
                table_html = page.content()
                df = pd.read_html(table_html)[0]

                # Extract links from the Name column
                print("Extracting report URLs...")
                logger.info("Extracting report URLs from the table.")
                links = page.query_selector_all('table#DataTables_Table_0 tbody tr td a')
                report_urls = []
                for link in links:
                    href = link.get_attribute('href')
                    if href:
                        # Ensure the href is a full URL
                        if href.startswith('/'):
                            full_url = base_url + href
                        else:
                            full_url = href
                        report_urls.append(full_url)
                    else:
                        report_urls.append('')

                # Add Report URL column
                df['Report URL'] = report_urls

                # Add 'Annoying' and 'Standard' columns based on URL
                df['Annoying'] = df['Report URL'].apply(lambda x: 'TRUE' if 'paper' in x.lower() else 'FALSE')
                df['Standard'] = df['Report URL'].apply(lambda x: 'TRUE' if 'annual' in x.lower() else 'FALSE')

                # Append to the all_data DataFrame
                all_data = pd.concat([all_data, df], ignore_index=True)

                print(f"Scraped page {page_number}")
                logger.info(f"Scraped page {page_number}")
                sys.stdout.flush()

                # Determine the next page number based on current page
                next_page_idx = page_number + 1

                # Construct the selector for the next page button
                # Example: For page 2, data-dt-idx="2"
                pagination_button_selector = f'a.paginate_button[data-dt-idx="{next_page_idx}"]'

                # Check if the next pagination button exists and is enabled
                next_button = page.query_selector(pagination_button_selector)
                if next_button:
                    class_attr = next_button.get_attribute('class')
                    if 'disabled' in class_attr:
                        # No more pages
                        print("No more pages. Exiting loop.")
                        logger.info("No more pages found. Scraping complete.")
                        break
                    else:
                        # Click the next pagination button
                        print(f"Clicking pagination button for page {next_page_idx}...")
                        logger.info(f"Clicking pagination button for page {next_page_idx}.")
                        next_button.click()
                        time.sleep(10)  # Wait for the next page to load
                        page_number += 1
                else:
                    # Pagination button not found, assume no more pages
                    print("Next pagination button not found. Exiting loop.")
                    logger.info("Next pagination button not found. Scraping complete.")
                    break

            # Define the column names based on the table structure
            # Adjust these names according to the actual table headers
            # Example column names; modify as needed
            columns = ['Filer', 'Year', 'Doc Type', 'District', 'Received', 'Report URL', 'Annoying', 'Standard']
            df_final = all_data.copy()
            df_final.columns = columns

            # Save the scraped data to a CSV file
            df_final.to_csv('house_disclosure_reports.csv', index=False)
            print("Data saved to house_disclosure_reports.csv")
            logger.info("Data saved to house_disclosure_reports.csv")
            sys.stdout.flush()

            # Optionally, return the DataFrame
            return df_final

        except Exception as e:
            print(f"An error occurred: {e}")
            logger.error(f"An error occurred: {e}")
            sys.stdout.flush()
        finally:
            # Close browser
            browser.close()

            
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



def run():
    get_all_house_disclosures()


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
