import os
import sys
import time
import json
import logging
import pytesseract
import pandas as pd
from pathlib import Path
from pdf2image import convert_from_path
import openai
import PyPDF2
import cv2
import numpy as np
import subprocess
from PIL import Image
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from tqdm import tqdm
from playwright.sync_api import sync_playwright, Page

# ----------------------------- Configuration ----------------------------- #

# Try to find tesseract in common installation paths
tesseract_paths = [
    "/usr/local/bin/tesseract",
    "/usr/bin/tesseract",
    "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "/opt/homebrew/bin/tesseract"
]

tesseract_found = False
for path in tesseract_paths:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        tesseract_found = True
        break

if not tesseract_found:
    raise RuntimeError("Tesseract is not installed or not found in common paths. Please install Tesseract and ensure it's in your PATH.")

# Configure OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set.")

# Configure logging to output to both console and analysis_logs.txt
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler('logs.txt')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ----------------------------- Utility Functions ----------------------------- #

def enhance_image_for_ocr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    return thresh

def is_valid_pdf(file_path: Path) -> bool:
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF'
    except Exception as e:
        logger.error(f"Error verifying PDF {file_path}: {e}")
        return False

def download_pdf_via_playwright(page: Page, url: str, download_dir: str, unique_id: int) -> Path:
    try:
        logger.info(f"Navigating to URL: {url}")
        page.goto(url, wait_until='networkidle', timeout=60000)
        time.sleep(2)  # Ensure page loads completely

        # Check if 'paper' is in the URL
        if "paper" in url.lower():
            # Click printer friendly button if it exists
            printer_friendly_url = url.replace('/view/', '/print/')
            logger.info(f"Navigating to printer-friendly URL: {printer_friendly_url}")
            page.goto(printer_friendly_url, wait_until='networkidle', timeout=60000)
            time.sleep(5)  # Wait for navigation to complete
            logger.debug(f"Navigated to Printer-Friendly page: {page.url}")

        # Export the page as PDF
        logger.info("Exporting page as PDF")
        filename = f"report_{unique_id}.pdf"
        filepath = Path(download_dir) / filename
        page.pdf(path=str(filepath), format="A4")
        logger.info(f"Exported PDF saved to: {filepath}")

        # Verify PDF integrity
        if is_valid_pdf(filepath):
            logger.info(f"Verified that {filepath} is a valid PDF.")
            return filepath
        else:
            logger.error(f"Downloaded file {filepath} is not a valid PDF.")
            return None

    except Exception as e:
        logger.error(f"Error downloading PDF from {url} via Playwright: {e}")
        return None

def download_html_via_playwright(page: Page, url: str, download_dir: str, unique_id: int) -> Path:
    try:
        logger.info(f"Navigating to URL: {url}")
        page.goto(url, wait_until='networkidle', timeout=60000)
        time.sleep(2)  # Ensure page loads completely

        # Get page content
        content = page.content()
        filename = f"report_{unique_id}.html"
        filepath = Path(download_dir) / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Downloaded HTML saved to: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error downloading HTML from {url} via Playwright: {e}")
        return None

def pdf_to_text_or_ocr(file_path: str) -> str:
    pdf_text = ""
    try:
        with open(file_path, 'rb') as file:
            try:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                logger.debug(f"Number of pages in PDF: {num_pages}")
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    page_text = page.extract_text()
                    if page_text:
                        pdf_text += page_text + "\n"
                    else:
                        logger.warning(f"No text extracted from page {page_num}. Falling back to OCR.")
                        images = convert_from_path(file_path, first_page=page_num, last_page=page_num)
                        for image in images:
                            open_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                            enhanced_image = enhance_image_for_ocr(open_cv_image)
                            ocr_text = pytesseract.image_to_string(enhanced_image)
                            pdf_text += ocr_text + "\n"
            except Exception as pdf_err:
                logger.warning(f"Error reading PDF structure: {pdf_err}. Attempting full OCR fallback.")
                images = convert_from_path(file_path)
                for image in images:
                    open_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    enhanced_image = enhance_image_for_ocr(open_cv_image)
                    ocr_text = pytesseract.image_to_string(enhanced_image)
                    pdf_text += ocr_text + "\n"
    except Exception as e:
        logger.error(f"Error processing PDF {file_path}: {e}")
    return pdf_text

def html_to_text(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            text = soup.get_text(separator='\n')
            return text
    except Exception as e:
        logger.error(f"Error processing HTML {file_path}: {e}")
        return ""

def analyze_text_chunk(text_chunk: str, prompt: str) -> dict:
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Respond only with a JSON object, no markdown formatting."},
        {"role": "user", "content": prompt},
        {"role": "user", "content": text_chunk}
    ]

    try:
        response = openai.chat.completions.create(
            model="gpt-4o", 
            messages=messages,
            temperature=0
        )

        # Extract the content of the assistant's message
        analysis_result = response.choices[0].message.content
        
        # Clean up the response by removing potential markdown formatting
        cleaned_result = analysis_result.strip()
        if cleaned_result.startswith('```'):
            # Remove markdown code block formatting
            cleaned_result = cleaned_result.split('\n', 1)[1]  # Remove first line with ```
            cleaned_result = cleaned_result.rsplit('\n', 1)[0]  # Remove last line with ```
            cleaned_result = cleaned_result.replace('```json', '').replace('```', '').strip()

        # Parse the cleaned JSON
        result = json.loads(cleaned_result)
        
        if result.get("found"):
            logger.info(f"Found assets: {result.get('assets')}")
            logger.info(f"Relevant quotes: {result.get('quotes')}")
        return result

    except json.JSONDecodeError as json_err:
        logger.error(f"JSON decode error: {json_err}")
        logger.error(f"Raw response content: {analysis_result if 'analysis_result' in locals() else 'No content received.'}")
        # Return a valid fallback response
        return {"found": False, "assets": [], "quotes": []}

    except Exception as e:
        logger.error(f"Unexpected error in analyze_text_chunk: {e}")
        return {"found": False, "assets": [], "quotes": []}

def merge_analysis_results(results: list) -> dict:
    merged = {
        "found": any(r["found"] for r in results),
        "assets": list(set(sum((r["assets"] for r in results), []))),
        "quotes": list(set(sum((r["quotes"] for r in results), [])))
    }
    # Log merged results if assets were found
    if merged["found"]:
        logger.info("Merged analysis results:")
        logger.info(f"All found assets: {merged['assets']}")
        logger.info(f"All relevant quotes: {merged['quotes']}")
    return merged

def analyze_content(content: str, is_pdf: bool) -> dict:
    prompt = (
        "This is a financial disclosure document. Identify ANY mentions of cryptocurrency assets or holdings using these matching rules:\n\n"
        "1. Search for cryptocurrency assets, including, but not limited to, the following assets:\n"
        "Bitcoin (BTC), Ethereum (ETH), Solana (SOL), BNB (BNB), Litecoin, Dogecoin (DOGE), XRP (XRP), Cardano (ADA), Pepe, Polkadot, Aptos, Uniswap, Stellar, Render, Bittensor, Tron (TRX), Shiba Inu (SHIB), Avalanche (AVAX), Toncoin (TON), Chainlink (LINK), iShares Bitcoin Trust ETF (IBIT), Grayscale Bitcoin Trust (GBTC), Grayscale Ethereum Trust (ETHE), ProShares Bitcoin Strategy ETF (BITO), ProShares Short Bitcoin Strategy ETF (BITI), Fidelity Wise Origin Bitcoin Fund (FBTC), ARK 21Shares Bitcoin ETF (ARKB), VanEck Digital Transformation ETF (DAPP), Invesco Alerian Galaxy Crypto Economy ETF (SATO), Fidelity Ethereum Fund ETF (FETH), ProShares Ether ETF (EETH), Velodrome (Velo)\n\n"
        "2. MATCH ALL VARIATIONS:\n"
        "- Split words (e.g., \"Doge Coin\", \"Bit Coin\")\n"
        "- Combined words (e.g., \"BitCoin\", \"DogeCoin\")\n" 
        "- Ticker only (\"BTC\", \"DOGE\", \"ETH\")\n"
        "- Prefixed/suffixed with \"coin\", \"token\", or \"crypto\"\n\n"
        "3. ALWAYS CHECK NEAR:\n"
        "- [ct], (ct), [crypto] notations\n"        
        "Return Dict format only:\n"
        "{\n"
        "    \"found\": True if assets located, else False,\n"
        "    \"assets\": [\"asset1\", \"asset2\", \"...\"],\n"
        "    \"quotes\": [\"quote1\", \"quote2\", \"...\"]\n"
        "}\n\n"
    )

    try:
        if is_pdf:
            chunk_size = 5000  # Adjusted for PDF content
        else:
            chunk_size = 5000  # Adjusted for HTML content

        text_chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        analysis_results = []

        for i, chunk in enumerate(text_chunks, start=1):
            try:
                logger.debug(f"Processing chunk {i}/{len(text_chunks)}.")
                chunk_result = analyze_text_chunk(chunk, prompt)
                analysis_results.append(chunk_result)
                time.sleep(1)  # Adjust sleep as needed
            except Exception as e:
                logger.error(f"Error processing chunk {i}/{len(text_chunks)}: {e}")

        if analysis_results:
            logging.info(analysis_results)
            return merge_analysis_results(analysis_results)
        else:
            logging.info("Didn't find anything")
            return {"found": False, "assets": [], "quotes": []}

    except Exception as e:
        logger.error(f"Error in analyze_content: {e}")
        return {"found": False, "assets": [], "quotes": []}

def analyze_reports(df: pd.DataFrame, page: Page) -> pd.DataFrame:
    df['Found'] = False
    df['Assets'] = ''
    df['Quotes'] = ''

    reports_dir = 'senate_reports'
    os.makedirs(reports_dir, exist_ok=True)

    logger.info("Starting download and analysis of reports...")

    for idx, row in tqdm(df.iterrows(), total=df.shape[0], desc="Processing Reports"):
        link = row.get('Report URL')

        if pd.notna(link) and link.strip():
            logger.info(f"Processing report {idx + 1}/{len(df)}: {link}")
            
            if "paper" in link.lower():
                # Download PDF via Playwright
                downloaded_file = download_pdf_via_playwright(page, link, reports_dir, unique_id=idx+1)
                if downloaded_file and downloaded_file.exists() and is_valid_pdf(downloaded_file):
                    file_path = downloaded_file
                    content = pdf_to_text_or_ocr(str(file_path))
                    analysis_data = analyze_content(content, is_pdf=True)

                    df.at[idx, 'Found'] = analysis_data.get('found', False)
                    df.at[idx, 'Assets'] = ', '.join(analysis_data.get('assets', []))
                    df.at[idx, 'Quotes'] = ' | '.join(analysis_data.get('quotes', []))

                    if analysis_data.get('found', False):
                        logger.info(f"Results for report {idx + 1}:")
                        logger.info(json.dumps(analysis_data, indent=4))
                        logger.info(f"Analysis completed for report {idx + 1}.")
                else:
                    logger.error(f"Failed to download or verify PDF for link: {link}")
            else:
                # Download HTML via Playwright
                downloaded_file = download_html_via_playwright(page, link, reports_dir, unique_id=idx+1)
                if downloaded_file and downloaded_file.exists():
                    file_path = downloaded_file
                    content = html_to_text(str(file_path))
                    analysis_data = analyze_content(content, is_pdf=False)

                    df.at[idx, 'Found'] = analysis_data.get('found', False)
                    df.at[idx, 'Assets'] = ', '.join(analysis_data.get('assets', []))
                    df.at[idx, 'Quotes'] = ' | '.join(analysis_data.get('quotes', []))

                    if analysis_data.get('found', False):
                        logger.info(f"Results for report {idx + 1}:")
                        logger.info(json.dumps(analysis_data, indent=4))
                        logger.info(f"Analysis completed for report {idx + 1}.")
                else:
                    logger.error(f"Failed to download HTML content for link: {link}")
        else:
            logger.warning(f"No valid link found for row {idx + 1}. Skipping.")

    return df

# ----------------------------- Main Function ----------------------------- #

def run_analysis():
    input_csv = 'senate_disclosures.csv'
    output_csv = 'senate_disclosures_analyzed.csv'

    try:
        logger.info(f"Reading input CSV: {input_csv}")
        if not os.path.exists(input_csv):
            logger.error(f"Input CSV file {input_csv} does not exist")
            sys.exit(1)
        df = pd.read_csv(input_csv)
        logger.info(f"Successfully read {len(df)} records.")
    except Exception as e:
        logger.error(f"Error reading CSV file {input_csv}: {e}")
        sys.exit(1)

    if 'Report URL' not in df.columns:
        logger.error("Input CSV must contain a 'Report URL' column with URLs to the PDF reports.")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        df = analyze_reports(df, page)
        browser.close()

    try:
        df.to_csv(output_csv, index=False)
        logger.info(f"Analysis completed. Results saved to {output_csv}.")
    except Exception as e:
        logger.error(f"Error saving to CSV file {output_csv}: {e}")

if __name__ == "__main__":
    run_analysis()
