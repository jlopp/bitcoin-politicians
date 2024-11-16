import csv
from config import source_data_dir
import pandas as pd
import os
import re
from collections import defaultdict

def add_link_to_source_file(last_name, first_name, state_abbr, filing_year, link):

    csv_file_path = os.path.join(source_data_dir, "source_data_links.csv")
    csv_columns = ["last_name", "first_name", "state", "filing_year", "link"]

    file_exists = os.path.isfile(csv_file_path)
    with open(csv_file_path, mode="a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=csv_columns)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "last_name": last_name,
            "first_name": first_name,
            "state": state_abbr,
            "filing_year": filing_year,
            "link": link
        })

def deduplicate_link_source_file():
    csv_file_path = os.path.join(source_data_dir, "source_data_links.csv")
    if not os.path.isfile(csv_file_path):
        print(f"No file found at {csv_file_path}")
        return
    
    df = pd.read_csv(csv_file_path)
    df = df.drop_duplicates()
    df.to_csv(csv_file_path, index=False)

def get_new_disclosures():
    source_file_path = os.path.join(source_data_dir, "source_data_links.csv")
    df = pd.read_csv(source_file_path)
    df_sorted = df.sort_values(by=['last_name', 'first_name', 'state', 'filing_year'], ascending=[True, True, True, False])
    current_disclosures = df_sorted.drop_duplicates(subset=['last_name', 'first_name', 'state'], keep='first')
    old_disclosures = df_sorted[~df_sorted['link'].isin(list(current_disclosures['link']))]

    common_identifiers = current_disclosures.merge(
        old_disclosures,
        on=['last_name', 'first_name', 'state'],
        how='inner'
    )[['last_name', 'first_name', 'state']]

    new_disclosures = current_disclosures.merge(
        common_identifiers,
        on=['last_name', 'first_name', 'state'],
        how='inner'
    )

    new_disclosures.to_csv('./new_disclosures.csv', index=False)
    current_disclosures.to_csv(source_file_path, index=False)

    print("\nNew disclosures since last run:")
    if len(new_disclosures): print(new_disclosures) 
    else: print('None')
    print('\n')

    return new_disclosures

def get_outdated_source_files(files):
    file_pattern = re.compile(r'(.+?)_(.+?)_(.+?)_(\d{4})_.+')
    parsed_files = []

    for file in files:
        match = file_pattern.match(file)
        if match:
            last_name, first_name, state, year = match.groups()
            parsed_files.append((last_name, first_name, state, int(year), file))

    grouped_files = defaultdict(list)
    for entry in parsed_files:
        grouped_files[(entry[0], entry[1], entry[2])].append(entry)

    outdated_files = []
    for key, entries in grouped_files.items():
        entries.sort(key=lambda x: x[3], reverse=True)
        outdated_files.extend(entry[4] for entry in entries[1:])
    
    return outdated_files
