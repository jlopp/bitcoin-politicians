import requests
import json
from typing import Any
from dataclasses import dataclass, asdict

from utils import BASE_DATA_FP, STATE_MAP, standardize_name

BASE_URL = f"https://api.congress.gov/v3"
API_KEY = "<enter-your-key>" # https://gpo.congress.gov/sign-up/

@dataclass
class Member:
    key: str
    full_name: str
    party: str
    state_district: str # Code for state and disctrict
    chamber: str # "House of Representatives" or "Senate"
    holdings: dict

def get_current_congress(params=None) -> int:
    url = BASE_URL + f'/congress/current'
    if params is None: params = {'api_key': API_KEY}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise requests.HTTPError(f"Received status code {response.status_code} when fetching members")

    data = response.json()

    return int(data['congress']['number'])

def get_members(congress: int, params=None) -> list[dict]:
    url = BASE_URL + f'/member/congress/{congress}'
    if params is None: params = {'api_key': API_KEY, 'limit': 250}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise requests.HTTPError(f"Received status code {response.status_code} when fetching members")

    data = response.json()
    assert 'members' in data, "no members were returned"

    members = [member for member in data['members']]

    # Update the URL to the next page
    if next_url := data['pagination'].get('next'):
        # Parse out the params from the next_url
        next_url_split = next_url.split('?')
        url = next_url_split[0]
        params.update(dict(x.split('=') for x in next_url_split[1].split('&')))
        members += get_members(congress, params)

    return members

def parse_members(members: list[dict]) -> list[Member]:
    # filter for if any members resigned during their term
    members = [member for member in members if any('endYear' not in term for term in member['terms']['item'])]

    ret = []
    for member in members:
        state = member['state'].title()
        state_district = f"{STATE_MAP.get(state, state)}{member.get('district', '')}"
        name: str = member['name'].split(',')
        # take the last name and the 2 first letters of the first name to use as key
        key = f"{standardize_name(name[0])}, {standardize_name(name[1])}"
        member_obj = Member(
            key=key,
            full_name=member['name'],
            party=member['partyName'][0],
            state_district=state_district,
            chamber=member['terms']['item'][-1]['chamber'],
            holdings={}
        )
        ret.append(member_obj)
    return ret

def setup_members(members: list[Member]):
    for member in members:
        member_fp = BASE_DATA_FP / member.chamber / member.key
        member_fp.mkdir(parents=True, exist_ok=True)

        json_fp = member_fp / f"{member_fp.name}.json"
        with open(json_fp, "w") as file:
            json.dump(asdict(member), file, indent=4)

def fetch_members(congress):
    return parse_members(get_members(congress))


if __name__ == "__main__":
    congress = get_current_congress()
    members = fetch_members(congress)
    setup_members(members)
