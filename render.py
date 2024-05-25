import json
import pandas as pd
from utils import HOUSE_DATA_FP, SENATE_DATA_FP

def _render_folder_markdown(json_paths):
    rows = []
    for path in json_paths:
        with open(path, "r") as f:
            data = json.load(f)

        full_name = data['full_name']

        for report, report_data in data.get('holdings', {}).items():
            data = report_data.get('data', [])
            link = report_data['link']
            date = report_data['date']
            for asset in data:
                rows.append((
                    full_name,
                    report,
                    f"[{date}]({link})",
                    asset['Asset'],
                    asset['Value'],
                ))

    # Convert the list of rows into a DataFrame
    df = pd.DataFrame(rows, columns=['full_name', 'report', 'date (link)', 'Asset', 'Value'])

    # Set MultiIndex
    df.set_index(['full_name'], inplace=True)
    return df.to_markdown()

def render_markdown():
    senate_json_paths = [path / f"{path.name}.json" for path in SENATE_DATA_FP.iterdir()]
    house_json_paths = [path / f"{path.name}.json" for path in HOUSE_DATA_FP.iterdir()]

    with open("sample_senate.md", "w") as f:
        f.write(_render_folder_markdown(senate_json_paths))

    with open("sample_house.md", "w") as f:
        f.write(_render_folder_markdown(house_json_paths))

