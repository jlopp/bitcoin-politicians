from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import pandas as pd
import time
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_total_pages(page):
    """
    Extract the total number of pages from the pagination section.
    """
    try:
        time.sleep(2)  # Wait for pagination to load
        pagination_buttons = page.query_selector_all('a.paginate_button')
        page_numbers = []
        for btn in pagination_buttons:
            text = btn.inner_text().strip()
            if text.isdigit():
                page_numbers.append(int(text))
        if page_numbers:
            total_pages = max(page_numbers)
            return total_pages
        else:
            return 1
    except Exception as e:
        logger.error(f"Error extracting total pages: {e}")
        return 1

def get_all_house_disclosures():
    """Retrieve all House financial disclosure filings for the most recent year."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set headless=True to run without a browser window
        page = browser.new_page()

        try:
            logger.info("Navigating to the House Financial Disclosure website...")
            page.goto('https://disclosures-clerk.house.gov/FinancialDisclosure')
            time.sleep(4)  # Wait for the page to load

            # Click the 'Search' link
            logger.info("Clicking the 'Search' link...")
            page.click('a[href="#Search"][data-custom-nav="sidenav"][data-view="ViewSearch"]')
            logger.info("'Search' link clicked.")
            time.sleep(4)  # Wait for the search section to render

            # Retrieve all filing years and select the most recent year
            logger.info("Retrieving filing years...")
            options = page.evaluate('Array.from(document.querySelectorAll("#FilingYear option")).map(o => o.value)')
            valid_years = [int(y) for y in options if y.isdigit()]
            if not valid_years:
                raise ValueError("No valid filing years found.")
            most_recent_year = str(max(valid_years))
            logger.info(f"Most recent filing year found: {most_recent_year}")

            # Select the most recent year from the dropdown
            logger.info(f"Selecting the filing year: {most_recent_year}")
            page.select_option('#FilingYear', most_recent_year)
            time.sleep(2)  # Brief pause to let the selection take effect

            # Click the 'Search' button
            logger.info("Clicking the 'Search' button...")
            search_button = page.get_by_role('button', name='Search')
            search_button.click()
            logger.info("'Search' button clicked.")
            time.sleep(4)  # Wait for search results to load

            # Determine the total number of pages
            total_pages = get_total_pages(page)
            logger.info(f"Total number of pages to process: {total_pages}")

            # Initialize a list to collect all data
            all_data = []
            base_url = 'https://disclosures-clerk.house.gov/'

            for current_page in range(1, total_pages + 1):
                logger.info(f"\nProcessing page {current_page} of {total_pages}...")
                time.sleep(4)  # Wait for the page to load

                # Extract table HTML and convert to DataFrame
                logger.info("Extracting table data...")
                try:
                    table_html = page.content()
                    df = pd.read_html(table_html)[0]
                except ValueError:
                    logger.warning("No table found on this page. Skipping...")
                    df = pd.DataFrame()

                # Extract report URLs from the 'Name' column
                logger.info("Extracting report URLs...")
                links = page.query_selector_all('table#DataTables_Table_0 tbody tr td a')
                report_urls = []
                for link in links:
                    href = link.get_attribute('href')
                    if href:
                        full_url = base_url + href
                        report_urls.append(full_url)
                    else:
                        report_urls.append('')  # Handle cases with no link

                # Add the 'Report URL' column to the DataFrame
                if not df.empty:
                    df['Report URL'] = report_urls
                    all_data.append(df)
                    logger.info(f"Collected {len(df)} records from page {current_page}.")
                else:
                    logger.info(f"No data found on page {current_page}.")

                # Navigate to the next page if not the last page
                if current_page < total_pages:
                    logger.info(f"Navigating to page {current_page + 1}...")
                    try:
                        # Click the pagination button based on the page number
                        pagination_button = page.query_selector(f'a.paginate_button:has-text("{current_page + 1}")')
                        if pagination_button:
                            pagination_button.click()
                            logger.info(f"Clicked on page {current_page + 1} button.")
                        else:
                            logger.warning(f"Pagination button for page {current_page + 1} not found.")
                            break
                    except PlaywrightTimeoutError:
                        logger.error("Timeout while trying to click the pagination button.")
                        break
                    except Exception as e:
                        logger.error(f"Error while attempting to click pagination button: {e}")
                        break
                else:
                    logger.info("Last page processed.")

            # Combine all DataFrames into one
            if all_data:
                combined_df = pd.concat(all_data, ignore_index=True)
                logger.info(f"\nTotal records collected: {len(combined_df)}")

                # Save the combined DataFrame to a CSV file
                combined_df.to_csv('house_disclosures.csv', index=False)
                logger.info("Data has been saved to 'house_disclosures.csv'.")
                return combined_df
            else:
                logger.warning("No data was collected.")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"An error occurred during processing: {e}")
        finally:
            # Ensure the browser is closed even if an error occurs
            browser.close()

def run():
    get_all_house_disclosures()

if __name__ == "__main__":
    run()
