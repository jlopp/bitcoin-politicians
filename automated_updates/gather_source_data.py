from congress_members import get_congress_members
from house import download_house_source_data_most_recent
from senate import download_senate_source_data_most_recent, start_chrome_driver
from organize_source_data import organize_source_data
import time
from config import chrome_driver_path
import os
os.makedirs('./cache', exist_ok=True)

start_time = time.time()

members = get_congress_members()
driver = start_chrome_driver(chrome_driver_path, headless=True)

no_disclosures = []
for i, member in enumerate(members):
    print(f'\n{i} / {len(members)}')
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

print(f'congress members missing disclosures: {len(no_disclosures)}')
print(no_disclosures)

print(f"\nData pull completed in {end_time - start_time:.2f} seconds.")

print('organizing source data...')
organize_source_data()