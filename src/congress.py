import os
import json 
import requests 
import logging

from dataclasses import dataclass
from typing import List, Dict, Optional 
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = os.getenv('CONGRESS_API_KEY')
            
def get_members(api_key: str) -> List[Dict]:
    """Get all members of Congress"""
    members = []
    api_url = 'https://api.congress.gov/v3/member'
    params = {
        'api_key': api_key,
        'limit': 250,
        'currentMember': 'true'
    }

    try: 
        while api_url:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            members.extend(data['members'])

            next_url = data.get('pagination', {}).get('next')
            if next_url:
                api_url = next_url
            else:
                api_url = None
        logger.info(f"Retrieved {len(members)} members")
        return members 
    
    except Exception as e:
        logger.error(f"Failed to retrieve members: {e}")
        return []

def save_members_to_json(members: List[Dict], filename: str):
    """
    Save members data to JSON file
    """
    try:
        with open(filename, 'w') as f:
            json.dump(members, f, indent=2)
        logger.info(f"Saved {len(members)} members to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Failed to save members to JSON: {e}")

def run():
    logger.info("Retrieving members...")
    members = get_members(api_key)
    if members:
        logger.info(f"First five members:\n {members[0:5]}")
        logger.info("Saving members file to json")
        filename = f"data/congress_members_{datetime.now().strftime('%Y-%m-%d')}.json"
        save_members_to_json(members, filename)
        logger.info(f"Members file saved to JSON: {filename}")
    else:
        logger.info("No members retrieved.")

if __name__ == "__main__":
    run()
