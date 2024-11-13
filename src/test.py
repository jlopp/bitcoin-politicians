import base64
from openai import OpenAI
from config import CRYPTO_ASSETS
from bs4 import BeautifulSoup

def quick_vision_test(file_path: str, file_type: str):
    """Analyze disclosure file based on specified type"""
    
    client = OpenAI()
    
    # Build prompt
    prompt = """
    This is a financial disclosure document. Find any terms mentioned that match or are similar to the following list. Be aware that matches may not be exact and may include misspellings, near-spellings, or variations due to difficult-to-read or ambiguous handwritten text. The search should be case-insensitive and tolerant of typographical errors.
    For instance, "Bob's Bank" might appear as "BankBOB", "Bobs Bank", or "Bobz Bank". "Bitcoin" might be written as "BitCOIN", "Bitcon", or "Bittcoin".
    Look for: """ + ', '.join(f"{a['name']} ({a['ticker']})" for a in CRYPTO_ASSETS['assets']) + """

    Format the response as JSON:
    {
        "found": true/false,
        "assets": [list of assets found],
        "quotes": [relevant text excerpts where the assets were found]
    }

    Do not return anything else.
    """
    
    if file_type == 'html':
        # Read local HTML file and strip tags
        with open(file_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            text = soup.get_text()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt + "\n\nContent:\n" + text}],
        )
        
    else:  # image or pdf
        if file_type == 'pdf':
            from pdf2image import convert_from_path
            pages = convert_from_path(file_path)
            # Save first page as temporary image
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp:
                pages[0].save(tmp.name, 'JPEG')
                # Load and encode the temp image
                with open(tmp.name, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        else:  # image
            with open(file_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", 
                         "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
        )
    
    print(response.choices[0].message.content)

# Example usage
if __name__ == "__main__":
    quick_vision_test("test.html", "html")     # Local HTML file
    # quick_vision_test("disclosure.pdf", "pdf")  # For PDF
    # quick_vision_test("disclosure.jpg", "image")  # For image