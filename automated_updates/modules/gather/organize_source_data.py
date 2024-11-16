import os
import pandas as pd
from modules.process.file_utils import split_pdf_to_jpeg, gif_to_jpeg
from tqdm import tqdm
import fitz  # PyMuPDF
from config import source_data_dir, house_messy_pdf_dir, house_clean_pdf_dir, senate_dir, processed_data_dir

def detect_house_clean_financial_disclosures_report(filepath):
    with fitz.open(filepath) as pdf:
        first_page_text = pdf[0].get_text()
        detection_text = first_page_text.lower().replace(" ", "")
        criteria1 = "Legislative Resource Center".lower().replace(" ", "") in detection_text
        criteria2 = "Clerk of the House of Representatives".lower().replace(" ", "") in detection_text
        
    return criteria1 and criteria2

def organize_source_data():
    # after source data is gathered into all_source_data,
    # sort it into separate folder w.r.t next data processing step
    
    for filename in tqdm(os.listdir(source_data_dir)):
        if filename in ['.DS_Store']: continue

        filepath = os.path.join(source_data_dir, filename)

        # For csv files, copy asset_names to processed_data_dir
        if filename.endswith('.csv'):
            data = pd.read_csv(filepath, usecols=[1], header=None)
            data.columns = ['asset_name']
            data.to_csv(os.path.join(processed_data_dir, filename), index=False)
        
        # gif files from senate
        elif os.path.isdir(filepath):
            # individual .gif files
            # some handwritten, ex. Lujan_NM_2024_senate
            # some electronic written, ex. Durbin_IL_2024_senate
            gif_filenames = sorted(os.listdir(filepath), key=lambda x: int(os.path.splitext(x)[0])) # sort numerically
            for gif_filename in gif_filenames:
                gif_to_jpeg(input_dir=filepath, 
                            filename=gif_filename, 
                            output_dir=senate_dir + filename)

        # pdf's from house source, multiple formats
        elif filename.endswith('.pdf'):
            # there are two pdf forms from the house of representatives. a clean one and a messy one
            # split them into different folders to be processed separately
            is_house_clean = detect_house_clean_financial_disclosures_report(filepath)
            is_house_messy = not is_house_clean # TODO: this works for now. would be more robust if we could detect both independently

            if is_house_clean:
                # Financial Disclosure Report with clean electronic text, ex. Adams_NC_2023_house.pdf
                split_pdf_to_jpeg(input_dir=source_data_dir, 
                                filename=filename, 
                                output_dir=house_clean_pdf_dir + '/' + filename.replace('.pdf',''),
                                rotate_degrees=0)
            
            elif is_house_messy:
                # Financial Disclosure Report with messy scanned text, often handwritten, ex. Carter_LA_2023_house.pdf
                split_pdf_to_jpeg(input_dir=source_data_dir, 
                                filename=filename, 
                                output_dir=house_messy_pdf_dir + '/' + filename.replace('.pdf',''),
                                rotate_degrees=90)

            else:
                exit('unknown pdf type.')

        else:
            exit(f'unrecognized: {filename}')

if __name__ == '__main__':
    organize_source_data()