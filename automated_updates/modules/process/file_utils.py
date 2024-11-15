import os
from pdf2image import convert_from_path
from PIL import Image
import csv
from config import source_data_dir
import pandas as pd

def split_pdf_to_jpeg(input_dir, filename, output_dir, rotate_degrees=0):
    os.makedirs(output_dir, exist_ok=True)
    images = convert_from_path( os.path.join(input_dir, filename) )
    
    for i, image in enumerate(images):
        # rotate counterclockwise
        if rotate_degrees!=0: image = image.rotate(rotate_degrees, expand=True)
        output_jpeg_path = os.path.join(output_dir, f"{filename.replace('.pdf','')}_{i + 1}.jpeg")
        image.save(output_jpeg_path, "JPEG")


def gif_to_jpeg(input_dir, filename, output_dir):
    gif_path = os.path.join(input_dir, filename)
    gif_image = Image.open(gif_path)
    gif_image = gif_image.convert("RGB")
    gif_image = gif_image.convert("RGB")

    jpeg_filename = os.path.splitext(filename)[0] + ".jpeg"
    jpeg_path = os.path.join(output_dir, jpeg_filename)
    os.makedirs(output_dir, exist_ok=True)
    gif_image.save(jpeg_path, "JPEG")

    return jpeg_path

def add_link_to_source_file(last_name, state_abbr, filing_year, link):

    csv_file_path = os.path.join(source_data_dir, "source_data_links.csv")
    csv_columns = ["name", "state", "filing_year", "link"]

    # Ensure the CSV file exists and has a header
    file_exists = os.path.isfile(csv_file_path)
    with open(csv_file_path, mode="a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=csv_columns)

        if not file_exists:  # Write the header if the file is new
            writer.writeheader()

        # Append the new row
        writer.writerow({
            "name": last_name,
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

def make_directories():
    from config import source_data_dir, house_messy_pdf_dir, house_clean_pdf_dir, senate_dir, processed_data_dir

    os.makedirs('./cache', exist_ok=True)
    os.makedirs('./final_datasets', exist_ok=True)
    os.makedirs(source_data_dir, exist_ok=True)
    os.makedirs(house_messy_pdf_dir, exist_ok=True)
    os.makedirs(house_clean_pdf_dir, exist_ok=True)
    os.makedirs(senate_dir, exist_ok=True)
    os.makedirs(processed_data_dir, exist_ok=True)
