import base64
import json
import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import OpenAI


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "qwen/qwen3-vl-235b-a22b-instruct"
MAX_OUTPUT_TOKENS = 4096

ASSET_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "asset_extraction",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "assets": {
                    "type": "array",
                    "description": "Asset names transcribed verbatim from the disclosure",
                    "items": {"type": "string", "minLength": 1},
                }
            },
            "required": ["assets"],
            "additionalProperties": False,
        },
    },
}

load_dotenv()


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def _required_environment_variable(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be set in automated_updates/.env")
    return value


@lru_cache(maxsize=1)
def _client():
    return OpenAI(
        api_key=_required_environment_variable("OPENROUTER_API_KEY"),
        base_url=OPENROUTER_BASE_URL,
    )


def _model():
    return os.getenv("OPENROUTER_MODEL") or DEFAULT_OPENROUTER_MODEL


def _parse_assets(content):
    try:
        payload = json.loads(content)
    except (TypeError, json.JSONDecodeError) as error:
        raise RuntimeError("OpenRouter returned invalid asset-extraction JSON") from error

    if not isinstance(payload, dict) or set(payload) != {"assets"}:
        raise RuntimeError("OpenRouter response did not match the asset-extraction schema")

    assets = payload["assets"]
    if not isinstance(assets, list) or not all(isinstance(asset, str) for asset in assets):
        raise RuntimeError("OpenRouter response contained an invalid assets list")

    cleaned_assets = []
    for asset in assets:
        asset = asset.strip()
        if not asset:
            raise RuntimeError("OpenRouter response contained a blank asset name")
        if asset.casefold() == "none":
            continue
        cleaned_assets.append(asset)

    return cleaned_assets


def extract_assets(message, base64_image):
    response = _client().chat.completions.create(
        model=_model(),
        temperature=0,
        seed=0,
        max_tokens=MAX_OUTPUT_TOKENS,
        response_format=ASSET_RESPONSE_FORMAT,
        extra_body={"provider": {"require_parameters": True}},
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

    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("OpenRouter returned an empty response")
    return _parse_assets(content)
