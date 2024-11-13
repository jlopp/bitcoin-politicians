import requests
from tabulate import tabulate
import pickle
import os
from dotenv import load_dotenv

state_to_abbreviation = {
    'Alabama': 'AL',
    'American Samoa': 'AS',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'District Of Columbia': 'DC',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Guam': 'GU',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Northern Mariana Islands': 'MP',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Puerto Rico': 'PR',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virginia': 'VA',
    'Virgin Islands': 'VI',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY',
}

def get_congress_gov_api_key():
    load_dotenv()
    api_key = os.getenv('CONGRESS_GOV_API_KEY')
    return api_key

def get_congress_members(congress=118, limit=250, ignore_cache=True):
    # use the cache if available, use api only when needed
    # cache is nice to have for development, not necessary for user
    if not ignore_cache:
        cache_file = f'./cache/congress_{congress}_members.pkl'
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as file:
                members = pickle.load(file)
                print("congress members loaded from cache.")
                return members
    
    print('getting congress members from api.congress.gov...')
    api_key = get_congress_gov_api_key()
    base_url = f"https://api.congress.gov/v3/member/congress/{congress}"
    members = []
    # limit is number of items to return
    # default to 20
    # max is 250, and produces a great speedup when there are many pages
    params = {'api_key': api_key, 'limit': limit}
    url = base_url

    while url:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            break
        
        data = response.json()
        if 'members' not in data:
            print(f"Error: 'members' key not found in the response. Response: {data}")
            break
        
        for member in data['members']:
            members.append(member)
        
        # Update the URL to the next page
        next_url = data['pagination'].get('next')
        if next_url:
            # Parse out the params from the next_url
            next_url_split = next_url.split('?')
            url = next_url_split[0]
            params.update(dict(x.split('=') for x in next_url_split[1].split('&')))
        else:
            url = None

    members = sorted(members, key=lambda x: x['name'])
    members = parse_members(members)
    
    if not ignore_cache:
        with open(cache_file, 'wb') as file:
            pickle.dump(members, file)
            print("cached congress members for future use.")

    return members

def parse_members(members):
    parsed_members = []
    for member in members:
        name = member['name']
        party = member['partyName'][0]
        state = member['state'].title()
        state_abbreviated = state_to_abbreviation.get(state, state)
        terms = member['terms']['item']
        current_term = [term for term in terms if 'endYear' not in term.keys()]
        # ignore them if they resigned during their current term
        if not current_term:
            continue
        # extract the Chamber from the current term
        chamber = current_term[0]['chamber']
        chamber_shortened = chamber.split(maxsplit=1)[0]
        parsed_member = [
            name, 
            party, 
            state_abbreviated, 
            chamber_shortened,
            "-",
            "-",
            ""
        ]
        parsed_members.append(parsed_member)

    return parsed_members

def output_member_data_as_markdown(data):
    headers = [
        'Name',
        'Party',
        'State',
        'Chamber',
        'Bitcoin Owner',
        'Disclosure',
        'Notes'
    ]
    return tabulate(data, headers=headers, tablefmt='github')

# Example usage
if __name__ == '__main__':
    congress_members = get_congress_members(congress=118)
    print(len(congress_members))
    #print(output_member_data_as_markdown(congress_members))