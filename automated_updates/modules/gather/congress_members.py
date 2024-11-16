import requests
from tabulate import tabulate
import pickle
import os
from dotenv import load_dotenv
from datetime import date

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
    import sys
    load_dotenv()
    api_key = os.getenv('CONGRESS_GOV_API_KEY')
    if api_key is None:
        print("Error: CONGRESS_GOV_API_KEY not found in environment variables.")
        sys.exit(1)  # Exits with an error code
    return api_key

def get_current_congress_number():
    base_congress = 118
    base_year = 2023
    today = date.today()
    
    # Calculate the offset based on the current year
    # Every Congress lasts 2 years starting from base_year
    congress = base_congress + (today.year - base_year) // 2
    
    # If today's date is before January 3 of the current odd year, subtract 1
    if today < date(base_year + (today.year - base_year) // 2 * 2, 1, 3):
        congress -= 1
    
    return congress

# take and modified from user dreslan at https://github.com/jlopp/bitcoin-politicians/issues/36
def get_congress_members(limit=250, ignore_cache=True, test_set=False):
    congress = get_current_congress_number() # get congress number to match biennial Jan 3 cycle
    
    # hitting the api takes a few seconds. nice to have this cached for faster development, not necessary for user
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

    if test_set:
        # Use a test set that will hit all code paths:
        test_set_names = [
            'Amo, Gabe', 'Thanedar, Shri', # house clean
            'Van Drew, Jefferson', # house messy
            'Vance, J. D.', # senate easy extract
            'Markey, Edward J.', # senate gifs
        ]
        members = [member for member in members if member[0] in test_set_names]
    
        print('using test set:')
        for member in members: print(member)

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
    congress_members = get_congress_members()
    print(congress_members)
    #print(output_member_data_as_markdown(congress_members))