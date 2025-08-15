import base64
from openai import OpenAI
from dotenv import load_dotenv
import os
# import backoff # can use backoff if you have low usage limits

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# @backoff.on_exception(backoff.expo, openai.RateLimitError)
def send_to_api(message, base64_image, model='gpt-5-mini'):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
    )
    return response.choices[0].message.content