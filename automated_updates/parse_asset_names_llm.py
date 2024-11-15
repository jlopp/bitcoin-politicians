# Part 2 of the pipeline: uses OpenAI multimodal endpoint to parse images

from config import house_clean_pdf_dir, house_messy_pdf_dir, senate_dir, processed_data_dir
from modules.process.parse_house_clean_llm import assets_from_house_clean_to_csv_entire_folder
from modules.process.parse_house_messy_llm import assets_from_house_messy_to_csv_entire_folder
from modules.process.parse_senate_llm import assets_from_senate_to_csv_entire_folder
# TODO: these parse files share a lot of code. 
# could all be the same module, dynamically get paths and prompts

import os

total_folders = 0
processed_folders = 0

# Count total folders in all directories
for root, dirs, files in os.walk(house_clean_pdf_dir): total_folders += len(dirs)
for root, dirs, files in os.walk(house_messy_pdf_dir): total_folders += len(dirs)
for root, dirs, files in os.walk(senate_dir): total_folders += len(dirs)

existing_outputs = [output.replace('.csv','') for output in os.listdir(processed_data_dir)]

# TODO: this should be parallelized, bottleneck will be OpenAI usage tier
# Process folders in house_clean_pdf_dir
for root, dirs, files in os.walk(house_clean_pdf_dir):
    for folder in dirs:
        processed_folders += 1
        print(f"Progress: {processed_folders} / {total_folders}")
        if folder in existing_outputs: continue
        folder_path = os.path.join(root, folder)
        print(f"\nProcessing folder in house_clean_pdf_dir: {folder_path}")
        assets_from_house_clean_to_csv_entire_folder(folder_path)

# # Process folders in house_messy_pdf_dir
for root, dirs, files in os.walk(house_messy_pdf_dir):
    for folder in dirs:
        processed_folders += 1
        print(f"Progress: {processed_folders} / {total_folders}")
        if folder in existing_outputs: continue
        folder_path = os.path.join(root, folder)
        print(f"\nProcessing folder in house_messy_pdf_dir: {folder_path}")
        assets_from_house_messy_to_csv_entire_folder(folder_path)

# Process folders in senate_dir
for root, dirs, files in os.walk(senate_dir):
    for folder in dirs:
        processed_folders += 1
        print(f"Progress: {processed_folders} / {total_folders}")
        if folder in existing_outputs: continue
        folder_path = os.path.join(root, folder)
        print(f"\nProcessing folder in senate_dir: {folder_path}")
        assets_from_senate_to_csv_entire_folder(folder_path)

print('\n')