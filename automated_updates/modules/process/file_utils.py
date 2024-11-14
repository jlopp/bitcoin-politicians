import os
from pdf2image import convert_from_path
from PIL import Image

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

def make_directories():
    from config import source_data_dir, house_messy_pdf_dir, house_clean_pdf_dir, senate_dir, processed_data_dir

    os.makedirs('./cache', exist_ok=True)
    os.makedirs('./final_datasets', exist_ok=True)
    os.makedirs(source_data_dir, exist_ok=True)
    os.makedirs(house_messy_pdf_dir, exist_ok=True)
    os.makedirs(house_clean_pdf_dir, exist_ok=True)
    os.makedirs(senate_dir, exist_ok=True)
    os.makedirs(processed_data_dir, exist_ok=True)
