# Part 2 of the pipeline: uses OpenAI multimodal endpoint to parse images

from config import house_clean_pdf_dir, house_messy_pdf_dir, senate_dir, processed_data_dir, source_data_dir
from modules.process.parse_house_clean_llm import assets_from_house_clean_to_csv_entire_folder
from modules.process.parse_house_messy_llm import assets_from_house_messy_to_csv_entire_folder
from modules.process.parse_senate_llm import assets_from_senate_to_csv_entire_folder
from modules.gather.source_file_links import get_outdated_source_files
# TODO: these parse files share a lot of code. 
# could all be the same module, dynamically get paths and prompts

import os
import argparse
import pandas as pd

total_folders = 0
processed_folders = 0

# Count total folders in all directories
for root, dirs, files in os.walk(house_clean_pdf_dir): total_folders += len(dirs)
for root, dirs, files in os.walk(house_messy_pdf_dir): total_folders += len(dirs)
for root, dirs, files in os.walk(senate_dir): total_folders += len(dirs)

parser = argparse.ArgumentParser()
parser.add_argument('--new-only', action='store_true', help='Only parse new disclosures since last run (stored in new_disclosures.csv)')
args = parser.parse_args()
if args.new_only:
    new_disclosures = pd.read_csv('./new_disclosures.csv')
    new_disclosure_names = [
        f"{row['last_name']}_{row['first_name']}_{row['state']}_{row['filing_year']}" 
        for _, row in new_disclosures.iterrows()
    ]
else: 
    new_disclosure_names = []

existing_outputs = [output.replace('.csv','') for output in os.listdir(processed_data_dir)]
outdated_files = [file.replace('.pdf','') for file in get_outdated_source_files(os.listdir(source_data_dir))]
skips = existing_outputs + outdated_files

# TODO: this should be parallelized, bottleneck will be OpenAI usage tier
# Process folders in house_clean_pdf_dir
root = next(os.walk(house_clean_pdf_dir))[0]
dirs = sorted(next(os.walk(house_clean_pdf_dir))[1])
for folder in dirs:
    processed_folders += 1
    print(f"\nProgress: {processed_folders} / {total_folders}")
    if folder in skips: continue
    if args.new_only and folder.replace('_house','').replace('_senate','') not in new_disclosure_names: continue

    folder_path = os.path.join(root, folder)
    print(f"\nProcessing folder in house_clean_pdf_dir: {folder_path}")
    assets_from_house_clean_to_csv_entire_folder(folder_path)

# Process folders in house_messy_pdf_dir
root = next(os.walk(house_messy_pdf_dir))[0]
dirs = sorted(next(os.walk(house_messy_pdf_dir))[1])
for folder in dirs:
    processed_folders += 1
    print(f"Progress: {processed_folders} / {total_folders}")
    if folder in skips: continue
    if args.new_only and folder.replace('_house','').replace('_senate','') not in new_disclosure_names: continue

    folder_path = os.path.join(root, folder)
    print(f"\nProcessing folder in house_messy_pdf_dir: {folder_path}")
    assets_from_house_messy_to_csv_entire_folder(folder_path)

# Process folders in senate_dir
root = next(os.walk(senate_dir))[0]
dirs = sorted(next(os.walk(senate_dir))[1])
for folder in dirs:
    processed_folders += 1
    print(f"Progress: {processed_folders} / {total_folders}")
    if folder in skips: continue
    if args.new_only and folder.replace('_house','').replace('_senate','') not in new_disclosure_names: continue

    folder_path = os.path.join(root, folder)
    print(f"\nProcessing folder in senate_dir: {folder_path}")
    assets_from_senate_to_csv_entire_folder(folder_path)

print('\n')