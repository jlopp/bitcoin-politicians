import os
import sys
import time
import json
import base64
import logging
import tempfile
import requests
import pandas as pd
from pathlib import Path
from pdf2image import convert_from_path
import openai
from math import ceil
import PyPDF2

from config import CRYPTO_ASSETS

# Configure OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure logging to output to both console and logs.txt
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)  # Console handler set to INFO

file_handler = logging.FileHandler('logs.txt')
file_handler.setLevel(logging.DEBUG)  # File handler set to DEBUG

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

def analyze_text_chunk(text_chunk, prompt):
    """
    Analyze a chunk of text using GPT-4o.
    
    Args:
        text_chunk (str): Text chunk to analyze
        prompt (str): The analysis prompt
        
    Returns:
        dict: Analysis results
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
        {"role": "user", "content": text_chunk}
    ]

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # Ensure this is the correct model
            messages=messages,
            temperature=0
        )
        
        # Log the entire response for debugging
        logger.debug(f"OpenAI API response: {response}")

        analysis_result = response.choices[0].message.content.strip()
        
        # Remove any markdown code block indicators
        analysis_result = analysis_result.replace('```json', '').replace('```', '').strip()
        
        # Validate that the response is likely JSON
        if not (analysis_result.startswith("{") and analysis_result.endswith("}")):
            logger.error(f"Unexpected response format: {analysis_result}")
            return {"found": False, "assets": [], "quotes": []}
        
        # Attempt to parse the JSON
        return json.loads(analysis_result)
    
    except json.JSONDecodeError as json_err:
        logger.error(f"JSON decode error: {json_err}")
        logger.error(f"Raw response content: {analysis_result if 'analysis_result' in locals() else 'No content received.'}")
        return {"found": False, "assets": [], "quotes": []}
    
    except Exception as e:
        logger.error(f"Unexpected error in analyze_text_chunk: {e}")
        return {"found": False, "assets": [], "quotes": []}

def merge_analysis_results(results):
    """
    Merge multiple analysis results into one.
    
    Args:
        results (list): List of analysis result dictionaries
        
    Returns:
        dict: Merged analysis results
    """
    merged = {
        "found": any(r["found"] for r in results),
        "assets": list(set(sum((r["assets"] for r in results), []))),
        "quotes": list(set(sum((r["quotes"] for r in results), [])))
    }
    return merged

def quick_vision_test(file_path: str, file_type: str = 'pdf') -> dict:
    """
    Analyze disclosure file based on specified type using OpenAI's GPT-4o model.

    Args:
        file_path (str): Path to the file to be analyzed.
        file_type (str): Type of the file ('pdf').

    Returns:
        dict: Analysis results containing 'found', 'assets', and 'quotes'.
    """
    # Build prompt
    prompt = f"""
    This is a financial disclosure document. Identify any terms that match or are similar to the following list. Matches may include misspellings, near-spellings, or variations due to difficult-to-read or ambiguous handwritten text. The search should be case-insensitive and tolerant of typographical errors.
    For example, "Bob's Bank" might appear as "BankBOB", "Bobs Bank", or "Bobz Bank". "Bitcoin" might be written as "BitCOIN", "Bitcon", or "Bittcoin".
    Look for: {', '.join(f"{a['name']} ({a['ticker']})" for a in CRYPTO_ASSETS['assets'])}

    Please provide your response in the following JSON format only, without any additional text:

    {{
        "found": true,
        "assets": [list of assets found],
        "quotes": [relevant text excerpts where the assets were found]
    }}
    """

    try:
        if file_type == 'pdf':
            # Extract text from PDF
            pdf_text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    page_text = page.extract_text()
                    if page_text:
                        pdf_text += page_text
                    else:
                        logger.warning(f"No text extracted from page {page_num} of {file_path}.")

            # Process text in chunks of 50,000 characters
            chunk_size = 50000
            text_chunks = [pdf_text[i:i+chunk_size] for i in range(0, len(pdf_text), chunk_size)]
            analysis_results = []

            for i, chunk in enumerate(text_chunks):
                try:
                    logger.debug(f"Processing chunk {i+1}/{len(text_chunks)}.")
                    chunk_result = analyze_text_chunk(chunk, prompt)
                    analysis_results.append(chunk_result)
                    time.sleep(1.5)  # Rate limiting between chunks
                except Exception as e:
                    logger.error(f"Error processing chunk {i+1}/{len(text_chunks)}: {e}")

            # Merge results from all chunks
            if analysis_results:
                return merge_analysis_results(analysis_results)
            else:
                return {"found": False, "assets": [], "quotes": []}

        else:
            logger.error(f"Unsupported file type: {file_type}")
            return {"found": False, "assets": [], "quotes": []}

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for {file_path}: {e}")
        return {"found": False, "assets": [], "quotes": []}
    except Exception as e:
        logger.error(f"Error in quick_vision_test for {file_path}: {e}")
        return {"found": False, "assets": [], "quotes": []}

def download_report(report_url: str, download_dir: str = 'reports') -> Path:
    """
    Download the report PDF from the given URL.

    Args:
        report_url (str): URL of the report to download.
        download_dir (str): Directory to save the downloaded reports.

    Returns:
        Path: Path to the downloaded report file, or None if failed.
    """
    try:
        os.makedirs(download_dir, exist_ok=True)
        response = requests.get(report_url, timeout=30)
        if response.status_code == 200:
            filename = report_url.split('/')[-1]
            file_path = Path(download_dir) / filename
            with open(file_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Downloaded report: {file_path}")
            return file_path
        else:
            logger.error(f"Failed to download report from {report_url}. Status code: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error downloading report from {report_url}: {e}")
        return None

def analyze_reports(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze each report in the DataFrame and add 'Found', 'Assets', 'Quotes' columns.

    Args:
        df (pd.DataFrame): DataFrame with 'Report URL' column.

    Returns:
        pd.DataFrame: Updated DataFrame with new columns.
    """
    # Initialize new columns
    df['Found'] = False
    df['Assets'] = ''
    df['Quotes'] = ''

    # Directory to store downloaded reports
    reports_dir = 'reports'
    os.makedirs(reports_dir, exist_ok=True)

    for idx, row in df.iterrows():
        report_url = row['Report URL']
        if pd.notna(report_url) and report_url.strip():
            logger.info(f"Processing report {idx + 1}/{len(df)}: {report_url}")
            file_path = download_report(report_url, download_dir=reports_dir)
            if file_path:
                # Since all reports are PDFs
                file_type = 'pdf'

                # Analyze the report
                analysis_data = quick_vision_test(str(file_path), file_type)

                # Update the DataFrame with analysis results
                df.at[idx, 'Found'] = analysis_data.get('found', False)
                df.at[idx, 'Assets'] = ', '.join(analysis_data.get('assets', []))
                df.at[idx, 'Quotes'] = ' | '.join(analysis_data.get('quotes', []))

                # Only display results if assets were found
                if analysis_data.get('found', False):
                    logger.info(f"Results for report {idx + 1}:")
                    logger.info(json.dumps(analysis_data, indent=4))
                    logger.info(f"Analysis completed for report {idx + 1}.")

                # Add sleep of 1.5 seconds between requests
                time.sleep(1.5)
        else:
            logger.warning(f"No valid report URL found for row {idx + 1}. Skipping.")

    return df

def run_analysis():
    """
    Main function to read the CSV, analyze reports, and save the augmented CSV.
    """
    input_csv = 'house_disclosures.csv'
    output_csv = 'house_disclosures_with_analysis.csv'

    try:
        logger.info(f"Reading input CSV: {input_csv}")
        df = pd.read_csv(input_csv)
        logger.info(f"Successfully read {len(df)} records.")
    except Exception as e:
        logger.error(f"Error reading CSV file {input_csv}: {e}")
        sys.exit(1)

    # Analyze the reports and update the DataFrame
    logger.info("Starting analysis of reports...")
    df = analyze_reports(df)

    # Save the updated DataFrame to a new CSV
    try:
        df.to_csv(output_csv, index=False)
        logger.info(f"Analysis completed. Results saved to {output_csv}.")
    except Exception as e:
        logger.error(f"Error saving to CSV file {output_csv}: {e}")

if __name__ == "__main__":
    run_analysis()
