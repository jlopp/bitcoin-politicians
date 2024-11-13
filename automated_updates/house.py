import requests
from bs4 import BeautifulSoup
from datetime import datetime
import unicodedata

def remove_accents(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def download_house_source_data_specific_year(last_name, state_abbr, filing_year):
    search_url = "https://disclosures-clerk.house.gov/FinancialDisclosure/ViewMemberSearchResult"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    }

    form_data = {
        'LastName': last_name,
        'FilingYear': filing_year,
        'State': state_abbr,
    }
    
    with requests.Session() as session:
        response = session.post(search_url, data=form_data, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        pdf_link = None
        
        table = soup.find("table", class_="library-table")
        if table:
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if not cols:
                    continue  # Skip header rows
                if len(cols) >= 4:
                    filing = cols[3].get_text(strip=True)  # 'Filing' is the 4th column (index 3)
                    if filing == "FD Original" or filing == "New Filer":
                        link_tag = row.find("a", href=True)
                        if link_tag:
                            pdf_link = f"https://disclosures-clerk.house.gov/{link_tag['href']}"
                            break  # Stop after finding the FD Original document
            if pdf_link:
                pdf_response = session.get(pdf_link)
                pdf_response.raise_for_status()

                filename = f"./source_data/{last_name}_{state_abbr}_{filing_year}_house.pdf"
                with open(filename, 'wb') as pdf_file:
                    pdf_file.write(pdf_response.content)
                print(f"\033[32mDownloaded {filename}\033[0m")
                return True
            else:
                return False
        else:
            return False

def download_house_source_data_most_recent(last_name, first_name, state_abbr):
    current_year = datetime.now().year
    for year in range(current_year, current_year - 5, -1):
        success = download_house_source_data_specific_year(last_name=last_name, state_abbr=state_abbr, filing_year=year)
        if success:
            return True
    
    ## try different variations of the name
    # normalize accented characters
    if last_name != remove_accents(last_name):
        last_name = remove_accents(last_name)
        return download_house_source_data_most_recent(last_name, first_name, state_abbr)
    
    # use second part of multipart last name
    if '-' in last_name:
        last_name = last_name.replace('-', ' ')
        return download_house_source_data_most_recent(last_name, first_name, state_abbr)
    
    # use second part of multipart last name
    if ' ' in last_name:
        last_name = last_name.split(' ')[1]
        return download_house_source_data_most_recent(last_name, first_name, state_abbr)
    
    # add second part of multipart first name to last name
    if ' ' in first_name:
        last_name = first_name.split(' ')[-1] + ' ' + last_name
        first_name = first_name.split(' ')[0]
        return download_house_source_data_most_recent(last_name, first_name, state_abbr)

    return False

if __name__ == '__main__':
    download_house_source_data_specific_year(last_name='Bilirakis', state_abbr='FL', filing_year=2023)