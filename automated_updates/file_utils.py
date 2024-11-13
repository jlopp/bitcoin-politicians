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
    os.makedirs('./cache', exist_ok=True)
    os.makedirs('./all_processed_data', exist_ok=True)
    os.makedirs('./intermediate_files/house_clean_intermediate_files', exist_ok=True)
    os.makedirs('./intermediate_files/house_messy_intermediate_files', exist_ok=True)
    os.makedirs('./intermediate_files/senate_intermediate_files', exist_ok=True)
