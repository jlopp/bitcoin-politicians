from collections import defaultdict
import unicodedata
import json
from pathlib import Path
import shutil
import re

def remove_directory(path:Path):
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        return True
    raise FileExistsError(f"directory {path} does not exist")

def update_holding_json(path_to_json:Path, holdings:dict):
    assert path_to_json.exists(), f"{path_to_json} does not exist"
    with open(path_to_json, "r") as file:
        data = json.load(file)

    data['holdings'] = data['holdings'] | holdings

    with open(path_to_json, "w") as file:
        json.dump(data, file, indent=4)

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

def standardize_name(full_name: str):
    full_name = remove_accents(full_name.strip()).upper()
    # Use regex to find the first word that doesn't end with a period
    match = re.search(r'\b(\w+)\b(?!\.\s|\.)', full_name)
    if match:
        # return match.group(1).strip()[:2]
        return match.group(1).strip()
    return full_name

def get_state_district_to_name_map():
    ret = {}
    for member in HOUSE_DATA_FP.iterdir():
        path = member / f"{member.name}.json"
        with open(path, "r") as file:
            data = json.load(file)
            ret[data['state_district']] = member.name
    for member in SENATE_DATA_FP.iterdir():
        path = member / f"{member.name}.json"
        with open(path, "r") as file:
            data = json.load(file)
            ret[data['state_district']] = member.name
    return ret

def _get_interchangable_names() -> dict[str, str]:
    p = Path(__file__).resolve().parent / "interchangable_names.json"
    with open(p, "r") as f:
        ret = json.load(f)
    reversed_dict = {value: key for key, value in ret.items()}
    ret |= reversed_dict
    assert len(ret) == len(reversed_dict) * 2, f"{len(ret)=}, {len(reversed_dict)=}"
    return ret

def interchange_name(full_name: str):
    interchangable_names_map = _get_interchangable_names()
    return interchangable_names_map.get(full_name, full_name)

def house_last_names() -> dict[str, list[str]]:
    ret = defaultdict(list)
    for path in HOUSE_DATA_FP.iterdir():
        last_name = path.name.split(",")[0].strip()
        ret[last_name].append(path.name)
    return ret

def senate_last_names() -> dict[str, list[str]]:
    ret = defaultdict(list)
    for path in SENATE_DATA_FP.iterdir():
        last_name = path.name.split(",")[0]
        ret[last_name].append(path.name)
    return ret

BASE_DATA_FP = Path(__file__).resolve().parent / 'data'
HOUSE_DATA_FP = BASE_DATA_FP / 'House of Representatives'
SENATE_DATA_FP = BASE_DATA_FP / 'Senate'

STATE_MAP = {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'Florida': 'FL',
    'Georgia': 'GA',
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
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY'
}

