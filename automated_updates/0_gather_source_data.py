# Part 1 of the pipeline: 
# Scrapes data from .gov sites and converts them to csv's when text is easily scrapable, and jpeg's when its not

# Source files may already be available from Github repo.
# Run this only if you want to re-pull most recent data

from modules.gather.congress_members import get_congress_members
from modules.gather.house_scrape import download_house_source_data_most_recent
from modules.gather.senate_scrape import download_senate_source_data_most_recent, start_chrome_driver
from modules.gather.organize_source_data import organize_source_data
from modules.process.file_utils import make_directories

import time
from dotenv import load_dotenv
import os
import argparse

make_directories()
load_dotenv()
chrome_driver_path = os.getenv('CHROME_DRIVER_PATH')

parser = argparse.ArgumentParser(description='Gather source data from Congress members.')
parser.add_argument('--test-set', action='store_true', help='Use small dataset with 20 congress members for testing. Make sure to delete existing all_source_data or change config.')
args = parser.parse_args()

members = get_congress_members(test_set=args.test_set)
driver = start_chrome_driver(chrome_driver_path, headless=True)

start_time = time.time()
no_disclosures = []
for i, member in enumerate(members):
    print(f'\n{i+1} / {len(members)}')
    name_parts = member[0].split(',')
    last_name = name_parts[0].strip()
    first_name_parts = name_parts[1].strip().split(' ')
    first_name = ' '.join(part for part in first_name_parts if len(part) > 1 or part.isalpha())

    party = member[1]
    state_abbr = member[2]
    house_senate = member[3]

    print(f'{first_name}, {last_name} {party} {state_abbr} {house_senate}')
    
    if house_senate == 'House':
        success = download_house_source_data_most_recent(last_name=last_name, first_name=first_name, state_abbr=state_abbr)
        if not success:
            print(f'\033[91m{first_name} {last_name} no disclosures found.\033[0m')
            no_disclosures.append(member)

    elif house_senate == 'Senate':
        success = download_senate_source_data_most_recent(driver, last_name, state_abbr)
        if not success:
            print(f'\033[91m{first_name} {last_name} no disclosures found.\033[0m')
            no_disclosures.append(member)

    else:
        exit(f'house_senate not recognized: {house_senate}')

end_time = time.time()

print('\n')
print(f'\033[38;5;208mcongress members missing disclosures: {len(no_disclosures)}\033[0m')
print(no_disclosures)
with open('missing_disclosures.txt', 'w') as f:
    for member in no_disclosures:
        f.write(f"{member}\n")

print(f"\nData pull completed in {end_time - start_time:.2f} seconds.")

print('organizing source data...')
organize_source_data()
print('\n')