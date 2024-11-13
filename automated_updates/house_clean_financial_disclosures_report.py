import fitz  # PyMuPDF
import re

def extract_asset_names(text):
    # Define a pattern to capture only asset names
    asset_name_pattern = r'([A-Za-z\s]+)\s+\[[A-Z]+\]'  # Asset name followed by a type in square brackets
    
    # Find all matches of asset names
    asset_names = re.findall(asset_name_pattern, text)
    
    # Remove any duplicate entries if necessary
    unique_asset_names = list(set(asset_names))
    
    return unique_asset_names
    
def detect_house_clean_financial_disclosures_report(filepath):
    with fitz.open(filepath) as pdf:
        first_page_text = pdf[0].get_text()
        detection_text = first_page_text.lower().replace(" ", "")
        criteria1 = "Legislative Resource Center".lower().replace(" ", "") in detection_text
        criteria2 = "Clerk of the House of Representatives".lower().replace(" ", "") in detection_text
        
    return criteria1 and criteria2