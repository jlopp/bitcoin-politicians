from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import argparse
import sys
import pandas as pd
from config import house_clean_pdf_dir, house_messy_pdf_dir, senate_dir, processed_data_dir, source_data_dir
from modules.process.parse_house_clean_llm import assets_from_house_clean_to_csv_entire_folder
from modules.process.parse_house_messy_llm import assets_from_house_messy_to_csv_entire_folder
from modules.process.parse_senate_llm import assets_from_senate_to_csv_entire_folder
from modules.gather.source_file_links import get_outdated_source_files

def process_folder(process_func, folder_path):
    process_func(folder_path)
    return folder_path

parser = argparse.ArgumentParser()
parser.add_argument('--new-only', action='store_true', help='Only parse new disclosures since last run (stored in new_disclosures.csv)')
parser.add_argument('--workers', type=int, default=8, help='Number of concurrent OpenRouter requests (default: 8)')
args = parser.parse_args()
if args.workers < 1:
    parser.error('--workers must be at least 1')

existing_outputs = [output.replace('.csv', '') for output in os.listdir(processed_data_dir)]
outdated_files = [file.replace('.pdf', '') for file in get_outdated_source_files(os.listdir(source_data_dir))]
skips = existing_outputs + outdated_files

if args.new_only:
    new_disclosures = pd.read_csv('./new_disclosures.csv')
    new_disclosure_names = [
        f"{row['last_name']}_{row['first_name']}_{row['state']}_{row['filing_year']}" 
        for _, row in new_disclosures.iterrows()
    ]
else:
    new_disclosure_names = []

tasks = []

def add_tasks(directory, process_func):
    root = next(os.walk(directory))[0]
    dirs = sorted(next(os.walk(directory))[1])
    for folder in dirs:
        if folder in skips:
            continue
        if args.new_only and folder.replace('_house', '').replace('_senate', '') not in new_disclosure_names:
            continue
        folder_path = os.path.join(root, folder)
        tasks.append((process_func, folder_path))

add_tasks(house_clean_pdf_dir, assets_from_house_clean_to_csv_entire_folder)
add_tasks(house_messy_pdf_dir, assets_from_house_messy_to_csv_entire_folder)
add_tasks(senate_dir, assets_from_senate_to_csv_entire_folder)

total_folders = len(tasks)
processed_folders = 0

failures = []

print(f'Running {args.workers} workers.')
with ThreadPoolExecutor(max_workers=args.workers) as executor:
    future_to_task = {executor.submit(process_folder, func, path): (func, path) for func, path in tasks}
    for future in as_completed(future_to_task):
        func, path = future_to_task[future]
        try:
            folder_path = future.result()
            processed_folders += 1
            print(f"\033[32mCompleted: {processed_folders} / {total_folders}\033[0m")
        except Exception as e:
            failures.append((path, str(e)))
            print(f"Error processing folder {path}: {e}", file=sys.stderr)

print('\n')

if failures:
    print(f"Failed to process {len(failures)} of {total_folders} folders.", file=sys.stderr)
    raise SystemExit(1)
