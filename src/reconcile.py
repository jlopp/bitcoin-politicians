import pandas as pd
import json
from typing import List, Dict
import openai
import time
import os 
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()


def load_congress_members(file_path: str) -> List[Dict]:
    """Load Congress members from JSON file"""
    with open(file_path, 'r') as f:
        members = json.load(f)
    return members

def create_gpt_prompt(member: Dict, disclosure_names: List[str]) -> str:
    """Create a prompt asking GPT to find the best match for a Congress member"""
    prompt = f"""Given the Congress member name "{member['name']}" ({member['state']}, {member['partyName']}), 
which of the following names (if any) refers to the same person? .
Names to check:
{', '.join(disclosure_names)}"""
    return prompt

def get_gpt_response(prompt: str, api_key: str) -> str:
    """Get response from ChatGPT"""
    client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are helping to match congressional names between different databases. Look for close matches, taking into account variations like middle initials, suffixes (Jr, Sr, III etc), and different formatting of the same name. If you find a likely match, return the matching name from the list. If no reasonable match exists, respond with 'NO MATCH'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error getting GPT response: {e}")
        return "ERROR"

def main():
    # Load data
    members = load_congress_members('congress_members.json')
    
    # Load disclosure files
    house_df = pd.read_csv('house_disclosures_analyzed.csv')
    senate_df = pd.read_csv('senate_disclosures_analyzed.csv')
    
    # Prepare senate names
    senate_df['Name'] = senate_df['First Name (Middle)'] + ' ' + senate_df['Last Name (Suffix)']
    
    # Combine all disclosure names
    all_disclosure_names = list(house_df['Name'].dropna().unique()) + list(senate_df['Name'].dropna().unique())
    
    # Load your API key
    
    # Create output structure
    matches = []
    
    # Process each member
    for member in tqdm(members, desc="Processing members"):
        prompt = create_gpt_prompt(member, all_disclosure_names)
        
        # Get GPT response with retry logic
        max_retries = 3
        for _ in range(max_retries):
            try:
                matched_name = get_gpt_response(prompt, api_key=os.getenv("OPENAI_API_KEY"))
                if matched_name != "ERROR":
                    break
                time.sleep(1)  # Wait before retry
            except Exception as e:
                print(f"Error processing {member['name']}: {e}")
                matched_name = "ERROR"
        
        # Store the match
        matches.append({
            'congress_name': member['name'],
            'state': member['state'],
            'party': member['partyName'],
            'matched_disclosure_name': matched_name,
            'chamber': member['terms']['item'][-1]['chamber'] if 'terms' in member else 'Unknown'
        })
        
        # Sleep to respect API rate limits
        time.sleep(0.5)
    
    # Convert matches to DataFrame
    matches_df = pd.DataFrame(matches)
    
    # Merge with disclosure data
    result = pd.DataFrame(matches)
    
    # Merge with house disclosures
    house_matches = result[result['matched_disclosure_name'].isin(house_df['Name'])]
    house_data = pd.merge(
        house_matches,
        house_df[['Name', 'Found', 'Assets', 'Quotes']],
        left_on='matched_disclosure_name',
        right_on='Name',
        how='left'
    )
    
    # Merge with senate disclosures
    senate_matches = result[result['matched_disclosure_name'].isin(senate_df['Name'])]
    senate_data = pd.merge(
        senate_matches,
        senate_df[['Name', 'Found', 'Assets', 'Quotes']],
        left_on='matched_disclosure_name',
        right_on='Name',
        how='left'
    )
    
    # Combine house and senate data
    final_data = pd.concat([house_data, senate_data])
    
    # Save results
    final_data.to_csv('gpt_matched_congress_data.csv', index=False)
    
    # Save matches for review
    matches_df.to_csv('name_matches.csv', index=False)
    
    print(f"Processed {len(members)} members.")
    print(f"Found {len(final_data)} matches.")
    print("Results saved to 'gpt_matched_congress_data.csv'")
    print("Name matches saved to 'name_matches.csv' for review")

if __name__ == "__main__":
    main()