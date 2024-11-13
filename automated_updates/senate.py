from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from datetime import datetime
import csv
import time
import os
import requests
from config import chrome_driver_path
from dotenv import load_dotenv

load_dotenv()
chrome_driver_path = os.getenv('CHROME_DRIVER_PATH')

def start_chrome_driver(chrome_driver_path, headless=True):
    chrome_options = webdriver.ChromeOptions()
    if headless: chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver

def download_senate_source_data_most_recent(driver, last_name, state_abbr):
    # beware, this gets ugly
    driver.set_window_size(1920, 1080)
    driver.get("https://efdsearch.senate.gov/search/")
    wait = WebDriverWait(driver, 600)
    agreement_checkboxes = driver.find_elements(By.ID, "agree_statement")
    if agreement_checkboxes: agreement_checkboxes[0].click()
    last_name_field = wait.until(EC.visibility_of_element_located((By.ID, "lastName")))
    last_name_field.clear()
    last_name_field.send_keys(last_name)
    senator_checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.senator_filer")))
    if not senator_checkbox.is_selected(): senator_checkbox.click()
    state_dropdown = Select(wait.until(EC.element_to_be_clickable((By.ID, "senatorFilerState"))))
    state_dropdown.select_by_value(state_abbr)
    annual_report_checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.report_types_annual")))
    if not annual_report_checkbox.is_selected(): annual_report_checkbox.click()
    submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    submit_button.click()
    date_received_column = wait.until(EC.element_to_be_clickable((By.XPATH, "//th[@aria-label='Date Received/Filed: activate to sort column ascending']")))
    date_received_column.click(); time.sleep(1)
    date_received_column.click(); time.sleep(1)
    wait.until(EC.presence_of_element_located((By.ID, "filedReports")))
    annual_report_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Annual Report') and not(contains(text(), 'Amendment')) and not(contains(text(), 'Extension'))]")
    if len(annual_report_links) == 0: return False

    report_links_with_dates = {}
    for link in annual_report_links:
        if "Annual Report" in link.text and "Amendment" not in link.text:
            date_cell = link.find_element(By.XPATH, "./ancestor::tr/td[last()]")
            date_text = date_cell.text.strip()
            report_date = datetime.strptime(date_text, "%m/%d/%Y")
            report_links_with_dates[report_date] = link
    
    if not report_links_with_dates: return False

    most_recent_date = max(report_links_with_dates.keys())
    most_recent_link = report_links_with_dates[most_recent_date]
    most_recent_link.click()

    wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Annual Report')]")))
    annual_report_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Annual Report') and not(contains(text(), 'Amendment'))]")
    report_url = annual_report_link.get_attribute("href")
    driver.get(report_url)
    #print(report_url)

    if 'view/annual' in report_url:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#grid_items tbody tr")))
        # scrape investment data from table, save to csv
        script = """
            var rows = [];
            document.querySelectorAll("#grid_items tbody tr").forEach(function(row) {
                var rowData = [];
                row.querySelectorAll("td").forEach(function(cell) {
                    rowData.push(cell.textContent.trim());
                });
                rows.push(rowData);
            });
            return rows;
        """

        filename = f"all_source_data/{last_name}_{state_abbr}_{most_recent_date.year}_senate.csv"
        rows = driver.execute_script(script)

        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(rows)
        print(f"\033[32mDownloaded {filename}\033[0m")
        return True

    elif 'paper' in report_url:
        # save gif files to folder
        image_elements = driver.find_elements(By.XPATH, "//img[contains(@src, '.gif')]")

        output_dir = f"./all_source_data/{last_name}_{state_abbr}_{most_recent_date.year}_senate"
        os.makedirs(output_dir, exist_ok=True)

        for idx, img_element in enumerate(image_elements):
            gif_url = img_element.get_attribute("src")
            
            response = requests.get(gif_url)
            if response.status_code == 200:
                gif_path = os.path.join(output_dir, f"{idx + 1}.gif")
                with open(gif_path, 'wb') as gif_file:
                    gif_file.write(response.content)

        print(f"\033[32mDownloaded files to {output_dir}\033[0m")
        return True
    
    else:
        exit('unrecognized url')

if __name__ == '__main__':
    driver = start_chrome_driver(chrome_driver_path=chrome_driver_path, headless=False)
    success = download_senate_source_data_most_recent(driver=driver, last_name='Ricketts', state_abbr='NE')