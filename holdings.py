from typing import Union
from dataclasses import dataclass
from bs4 import BeautifulSoup
from pdf2image import convert_from_bytes
from tqdm import tqdm
import zipfile
import io
import json
import requests

from utils import (
    HOR_DATA_FP,
    SENATE_DATA_FP,
    update_holding_json,
    remove_directory,
    standardize_name,
    interchange_name,
    house_last_names, senate_last_names
)
from members import Member



# =============================================
# ========= House of Representatives ==========
# =============================================
# https://disclosures-clerk.house.gov/

def download_zip(year: int):
    url = f"https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip"
    unzip_folder = HOR_DATA_FP / f"{year}FD"
    unzip_folder.mkdir(parents=True, exist_ok=True)

    response = requests.get(url)
    if response.status_code != 200:
        raise requests.HTTPError(f"Failed to download from {url}")

    zip_content = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_content, "r") as zip_ref:
        zip_ref.extractall(unzip_folder)

    print(f"Extracted files to {unzip_folder}")


def load_HoR_FD_XML(year: int) -> list[dict]:
    xml_fp = HOR_DATA_FP / f'{year}FD/{year}FD.xml'
    assert xml_fp.exists()

    with open(xml_fp, 'r') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'xml')

    fds = [{child.name: child.text.strip() if child.text else None for child in member.find_all()} \
           for member in soup.find_all('Member')]

    # 'FilingType': 'O' -> Annual Report
    # 'FilingType': 'H' -> New Filer Report
    fds = [fd for fd in fds if fd['FilingType'] in ['O', 'H']]

    if len(fds) == 0:
        raise RuntimeError(f"there are no Annual Reports for House of Representatives for {year=}")

    # remove the FD stuff
    remove_directory(HOR_DATA_FP / f'{year}FD')
    print(f"Removed files from {HOR_DATA_FP / f'{year}FD'}")

    return fds

def save_HoR_FD_PDF(year: int, fds: list[dict]):
    desc = "Scraping financial disclosures for members in House of Representatives"
    missed = []
    hit = []
    unsure = []
    last_names = house_last_names()
    for disclosure in tqdm(fds, desc=desc):
        # unpack
        last_name = standardize_name(disclosure['Last'])
        first_name = standardize_name(disclosure['First'])
        last_name, first_name = interchange_name(f"{last_name}, {first_name}").split(",")
        first_name = first_name.strip()
        last_name = last_name.strip()

        doc_id = disclosure['DocID']
        year = disclosure['Year']
        filing_date = disclosure['FilingDate'].replace('/', '-')
        pdf_link = f'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}/{doc_id}.pdf'

        key = f"{last_name}, {first_name}"
        member_fp = HOR_DATA_FP / key

        # missed
        if not member_fp.exists():
            missed.append(member_fp.name)
            # unsure
            if last_name in last_names:
                unsure.append((f"{last_name}, {first_name}", last_names[last_name]))
            continue

        # create folder for member and create a folder to store images
        images_fp = member_fp / doc_id
        images_fp.mkdir(parents=True, exist_ok=True)

        response = requests.get(pdf_link)
        if response.status_code != 200:
            raise requests.HTTPError(f"Failed to download {pdf_link}")

        images = convert_from_bytes(response.content)

        for i, image in enumerate(images):
            image_fp = images_fp / f"{filing_date}_{i}.jpg"
            image.save(image_fp, 'JPEG')

        # dump member json info
        json_data = {doc_id: {"data": [], "link": pdf_link, "date": filing_date}}
        json_fp = member_fp / f"{member_fp.name}.json"
        update_holding_json(json_fp, json_data)

        hit.append(member_fp.name)

    print(f"hit: {sorted(hit)}")
    print(f"missed: {sorted(missed)}")

    return unsure


def scrape_house_of_representatives(year: int) -> list:
    # download FD description
    download_zip(year=year)

    # scrape and load financial disclosures
    fds = load_HoR_FD_XML(year=year)

    # save to data/house_of_representatives/{year}
    unsure = save_HoR_FD_PDF(year=year, fds=fds)
    return unsure


# ===========================
# ========= Senate ==========
# ===========================
# https://efdsearch.senate.gov/search/

ROOT = 'https://efdsearch.senate.gov'
LANDING_PAGE_URL = f'{ROOT}/search/home/'
SEARCH_PAGE_URL = f'{ROOT}/search/'
REPORTS_URL = f'{ROOT}/search/report/data/'

BATCH_SIZE = 100

@dataclass
class SenateMember:
    first_name: str
    last_name: str
    html: str
    date: str
    is_scanned: bool

def _csrf(client: requests.Session) -> str:
    """ Set the session ID and return the CSRF token for this session. """
    landing_page_response = client.get(LANDING_PAGE_URL)
    assert landing_page_response.url == LANDING_PAGE_URL, 'Failed to fetch filings landing page'

    landing_page = BeautifulSoup(landing_page_response.text, 'lxml')
    form_csrf = landing_page.find(
        attrs={'name': 'csrfmiddlewaretoken'}
    )['value']
    form_payload = {
        'csrfmiddlewaretoken': form_csrf,
        'prohibition_agreement': '1'
    }
    client.post(LANDING_PAGE_URL,
                data=form_payload,
                headers={'Referer': LANDING_PAGE_URL})

    if 'csrftoken' in client.cookies:
        csrftoken = client.cookies['csrftoken']
    else:
        csrftoken = client.cookies['csrf']
    return csrftoken


def reports_api(client: requests.Session, offset: int, token: str, year: int) -> list[list[str]]:
    """ Query the periodic transaction reports API. """
    login_data = {
        'start': str(offset),
        'length': str(BATCH_SIZE),
        'report_types': '[7]', # Annual reports
        'filer_types': '[]', # 1 for Senator (not candidate)
        'submitted_start_date': f'01/01/{year} 00:00:00',
        'submitted_end_date': f'01/01/{year+1} 00:00:00',
        'candidate_state': '',
        'senator_state': '',
        'office_id': '',
        'first_name': '',
        'last_name': '',
        'csrfmiddlewaretoken': token
    }
    response = client.post(REPORTS_URL,
                           data=login_data,
                           headers={'Referer': SEARCH_PAGE_URL})
    return response.json()['data']

def disclosure_api(client: requests.Session, member: SenateMember, full_url: str):
    response = client.get(full_url)

    webpage_soup = BeautifulSoup(response.text, 'html.parser')

    # if the disclosure is scanned, we just fetch the images
    if member.is_scanned:
        gif_urls = [img['src'] for img in webpage_soup.find_all('img', class_='filingImage')]
        responses = [client.get(url) for url in gif_urls]
        if any(response.status_code != 200 for response in responses):
            raise requests.HTTPError(f"{member=} raise HTTP error")
        return [response.content for response in responses]

    # otherwise, we'll parse the webpage for assets
    assets_section = webpage_soup.find('h3', string='Part 3. Assets').find_parent('section')
    table = assets_section.find('table', {'id': 'grid_items'})

    ret = []
    for row in table.tbody.find_all('tr'):
        cells = row.find_all('td')
        asset_data = {
        'Asset': cells[1].find('strong').text.strip(), # strong -> only get bolded Asset title (no asset description)
        'Asset Type': cells[2].get_text(separator=" ").strip(),
        'Owner': cells[3].text.strip(),
        'Value': cells[4].text.strip(),
        'Income Type': cells[5].text.strip()[:-1],
        'Income': cells[6].text.strip(),
        }
        ret.append(asset_data)

    return ret


def scrape_and_save_disclosure(client: requests.Session, reports:list[SenateMember]) -> list:
    desc = "Scraping financial disclosures for members in Senate"
    hit = []
    missed = []
    unsure = []
    last_names = senate_last_names()
    for disclosure in tqdm(reports, desc=desc):
        key = f"{disclosure.last_name}, {disclosure.first_name}"
        disclosure_fp = SENATE_DATA_FP / key

        # missed
        if not disclosure_fp.exists():
            missed.append(disclosure_fp.name)
            # unsure
            if disclosure.last_name in last_names:
                unsure.append((f"{disclosure.last_name}, {disclosure.first_name}", last_names[disclosure.last_name]))
            continue

        # Find the <a> tag and extract the href attribute
        link_soup = BeautifulSoup(disclosure.html, 'html.parser')
        a_tag = link_soup.find('a')
        href_link = a_tag['href']
        disclosure_name = a_tag.text

        full_url = ROOT + href_link
        member_diclosure: list[Union[bytes, dict]] = disclosure_api(client, disclosure, full_url)

        if disclosure.is_scanned:
            assert all(isinstance(f, bytes) for f in member_diclosure), \
            f"datatype is wrong for {disclosure.html}"

            # create a folder to store images
            images_fp = disclosure_fp / disclosure_name
            images_fp.mkdir(parents=True, exist_ok=True)

            for i, f in enumerate(member_diclosure):
                file_fp = images_fp / f"{disclosure.date}_{i}.gif"
                with open(file_fp, "wb") as file:
                    file.write(f)

            json_data = {disclosure_name: {"data": [], "link": full_url, "date": disclosure.date}}
            json_fp = disclosure_fp / f"{disclosure_fp.name}.json"
            update_holding_json(json_fp, json_data)
        else:
            assert all(isinstance(f, dict) for f in member_diclosure), \
            f"datatype is wrong for {disclosure.html}"

            json_data = {disclosure_name: {"data": member_diclosure, "link": full_url, "date": disclosure.date}}
            json_fp = disclosure_fp / f"{disclosure_fp.name}.json"
            update_holding_json(json_fp, json_data)

        hit.append(disclosure_fp.name)

    print(f"hit: {sorted(hit)}")
    print(f"missed: {sorted(missed)}")

    return unsure

def scrape_senate(year: int):
    def _filter(reports: list[list[str]]) -> list[SenateMember]:
        ret = []
        for report in reports:
            if "Senator" in report[2]:
                first_name = standardize_name(report[0])
                last_name = standardize_name(report[1])
                last_name, first_name = interchange_name(f"{last_name}, {first_name}").split(",")
                ret.append(SenateMember(
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                    html=report[3],
                    date=report[4].replace("/", "-"),
                    is_scanned= "for CY" not in report[3]
                ))
        return ret

    client = requests.Session()

    token = _csrf(client)
    idx = 0
    reports = reports_api(client, idx, token, year)
    all_reports: list[list[str]] = []
    while len(reports) != 0:
        all_reports.extend(reports)
        idx += BATCH_SIZE
        reports = reports_api(client, idx, token, year)

    all_reports = _filter(all_reports)

    unsure = scrape_and_save_disclosure(client, all_reports)
    return unsure


if __name__ == "__main__":
    year = 2022

    # House of Representatives
    # -> /data/house_of_representatives/reports/{year}
    unsure = scrape_house_of_representatives(year)

    # Senate
    # -> /data/senate/reports/{year}
    unsure.extend(scrape_senate(year))

    for name_1, name_2 in unsure:
        print(name_1, " <=> ", name_2)