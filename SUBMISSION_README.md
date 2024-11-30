# Congressional Crypto Disclosure Analysis

A system for scraping, downloading, and analyzing cryptocurrency holdings disclosed in Congressional financial disclosures.

## Overview

This toolkit scrapes financial disclosures from both House and Senate websites, downloads the documents, extracts text content, and analyzes them for cryptocurrency holdings using GPT-4o.

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Install Tesseract OCR:
- Linux: `sudo apt-get install tesseract-ocr`
- Mac: `brew install tesseract`
- Windows: Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

4. Set up environment variables in `.env`:
```env
CONGRESS_API_KEY=your-congress-api-key
OPENAI_API_KEY=your-openai-api-key
```

## Usage

Run the complete pipeline:
```bash
python main.py
```

This will sequentially:
1. Scrape House disclosures
2. Analyze House documents for crypto holdings 
3. Scrape Senate disclosures
4. Analyze Senate documents for crypto holdings

Results are saved to `house_disclosures_analyzed.csv` and `senate_disclosures_analyzed.csv`

## Example Detection

Here's an example of a detected crypto holding from Rep. Mike Collins' Annual Disclosure:
```json
{
    "found": true,
    "assets": [
        "Velodrome"
    ],
    "quotes": [
        "Velodrome  [CT] S 06/24/2024 06/24/2024 $1,001 - $15,000"
    ]
}
```

## Project Structure

```
src/
  ├── house_scrape.py      # House disclosure website scraper
  ├── house_analysis.py    # House document analyzer
  ├── senate_scrape.py     # Senate disclosure website scraper
  ├── senate_analysis.py   # Senate document analyzer
  └── config.py           # Crypto asset configurations
main.py                  # Entry point
.env                     # Environment variables
```

## Technical Details

- Uses Playwright for web scraping
- PyPDF2 with Tesseract OCR fallback for text extraction
- GPT-4o for crypto asset detection
- Includes retry logic and rate limiting
- Comprehensive logging to console (INFO) and logs.txt (DEBUG)