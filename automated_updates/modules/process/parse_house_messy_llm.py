from modules.process.openai_wrapper import encode_image, send_to_api
from config import processed_data_dir

import csv
import os
import glob
import re

def assets_from_house_messy_image_to_csv(input_image_path):
	base64_image = encode_image(input_image_path)
	if False:
		# this idea was to skip pages that don't list assets. it is a waste of tokens and doesn't seem to hurt accuracy to just shove all pages
		response = send_to_api(message="is this the schedule A part of the form that lists assets? answer Y or N only.", 
							base64_image=base64_image)

		if response.lower() == 'n':
			# not schedule A, skip the page
			print('skipped')
			return []

	# use '|' separator to avoid characters in asset names
	response = send_to_api(message="get the asset names in the public disclosure form, return them in a | separated list only, no other commentary.", 
						   base64_image=base64_image, 
						   model="gpt-4o")
	asset_list = [response.strip() for response in response.split("|")]
	
	return asset_list

def assets_from_house_messy_to_csv_entire_folder(folder_path):
	folder_name = folder_path.split('/')[-1]
	combined_csv_path = processed_data_dir + f'{folder_name}.csv'
	os.makedirs(os.path.dirname(combined_csv_path), exist_ok=True)

	all_assets = []

	image_files = glob.glob(os.path.join(folder_path, "*.jpeg"))
	image_files = sorted(image_files, key=lambda x: int(re.search(r'_(\d+)\.jpeg', x).group(1)))
	
	for image_path in image_files:
		print(image_path)
		assets = assets_from_house_messy_image_to_csv(image_path)
		if len(assets):
			all_assets += assets

	with open(combined_csv_path, 'w', newline='') as csv_file:
		writer = csv.writer(csv_file)
		writer.writerow(["asset_name"])  # Header
		for asset in all_assets:
			writer.writerow([asset])

	return True

if __name__ == '__main__':
	folder_path = "./intermediate_files/house_messy_intermediate_files/Rogers_KY_2023_house"
	assets_from_house_messy_to_csv_entire_folder(folder_path)