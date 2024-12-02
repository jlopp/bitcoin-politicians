import openai
import google.generativeai as genai
import base64
import requests
from pathlib import Path

from utils import SENATE_DATA_FP, HOUSE_DATA_FP

# OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
model = genai.GenerativeModel('gemini-pro-vision')

# TODO: google.auth.exceptions.DefaultCredentialsError: Your default credentials were not found.
# To set up Application Default Credentials, see
# https://cloud.google.com/docs/authentication/external/set-up-adc for more information.
def google_chat_with_images(image_paths: list[Path]):
    def _encode_image(image_path):
        from PIL import Image
        image = Image.open(image_path).convert('RGB')
        return image.tobytes()

    images = [{
        'mime_type': 'image/jpeg',
        'data': encode_image(path)
    } for path in image_paths]

    few_shot_examples = [
        {
            "Asset": "Capital One",
            "Asset Type": "Bank Deposit",
            "Owner": "Joint",
            "Value": "$100,001 - $250,000",
            "Income Type": "Interest",
            "Income": "$201 - $1,000"
        },
        {
            "Asset": "Bank of America",
            "Asset Type": "Bank Deposit",
            "Owner": "Joint",
            "Value": "$1,001 - $15,000",
            "Income Type": "None",
            "Income": "None (or less than $201)"
        },
        {
            "Asset": "Bank of America",
            "Asset Type": "Bank Deposit",
            "Owner": "Joint",
            "Value": "$1,001 - $15,000",
            "Income Type": "None",
            "Income": "None (or less than $201)"
        },
    ]

    prompt = f"""
You are an assistant that extracts information from images and returns results in JSON format with the following structure:

{few_shot_examples}
"""

    response = model.generate_content(
        contents=[prompt, *images]
    )
    # print(response.resolve())

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def openai_chat_with_images(image_paths: list[str | Path], system_text: str, user_text: str):
    image_paths = [Path(path) if isinstance(path, str) else path for path in image_paths]
    base64_images = [encode_image(image_path) for image_path in image_paths]

    # add text
    content = [{
        "type": "text",
        "text": user_text
    }]

    # add images
    for base64_image in base64_images:
        content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })

    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": content}
    ]

    payload = {
        "model": "gpt-4o",
        "messages": messages,
        "max_tokens": 300
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()

def disclosure_openai_VLM(image_paths):
    # define few-shot structure
    few_shot_examples = [
        {
            "Asset": "Capital One",
            "Asset Type": "Bank Deposit",
            "Owner": "Joint",
            "Value": "$100,001 - $250,000",
            "Income Type": "Interest",
            "Income": "$201 - $1,000"
        },
        {
            "Asset": "Bank of America",
            "Asset Type": "Bank Deposit",
            "Owner": "Joint",
            "Value": "$1,001 - $15,000",
            "Income Type": "None",
            "Income": "None (or less than $201)"
        },
        {
            "Asset": "Bank of America",
            "Asset Type": "Bank Deposit",
            "Owner": "Joint",
            "Value": "$1,001 - $15,000",
            "Income Type": "None",
            "Income": "None (or less than $201)"
        },
    ]

    # TODO: maybe try fewshot in user_text
    # add few-shot to system_text
    system_text = f"""
You are an assistant that extracts information from images and returns results in JSON format with the following structure:

{few_shot_examples}
"""

    # user prompt
    user_text = "The images are from a financial disclosure of a congress member. Please extract the assets of the congress member for me in JSON format. Please make sure to only answer with the JSON."

    return openai_chat_with_images(image_paths, system_text, user_text)

if __name__ == "__main__":
    senate_folders = [f for f in SENATE_DATA_FP.iterdir() if f.is_dir()]
    hor_folders = [f for f in HOUSE_DATA_FP.iterdir() if f.is_dir()]

    senate_names = [f.name for f in senate_folders]
    hor_names = [f.name for f in hor_folders]

    senate_folders_with_images = [f for f in senate_folders if any(ff.is_dir() for ff in f.iterdir())]
    hor_folders_with_images = [f for f in hor_folders if any(ff.is_dir() for ff in f.iterdir())]

    # print([f.name for f in hor_folders_with_images])
    for folder in hor_folders_with_images:
        image_paths = [image for f in folder.iterdir() if f.is_dir() for image in f.iterdir()]
        google_chat_with_images(image_paths)

    # for folder in hor_folders_with_images:
    #     image_paths = [image for f in folder.iterdir() if f.is_dir() for image in f.iterdir()]
    #     print(disclosure_openai_VLM(image_paths))
    #     exit(0)
