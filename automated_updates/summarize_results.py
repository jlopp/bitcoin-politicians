# Part 3 of the pipeline: 
# Identifies bitcoin/crypto assets and combines files in all_processed_data into final dataframes

import os
import pandas as pd
from config import processed_data_dir, source_data_dir
from config import bitcoin_crypto_terms, bitcoin_crypto_terms_false_positives
from modules.gather.congress_members import get_congress_members

def combine_processed_data():
    dataframes = []
    
    for filename in os.listdir(processed_data_dir):
        if filename.endswith('.csv'):
            parts = filename.split('_')
            last_name = parts[0]
            first_name = parts[1]
            state = parts[2]
            year = parts[3]
            house_senate = parts[4].replace('.csv', '')

            file_path = os.path.join(processed_data_dir, filename)
            df = pd.read_csv(file_path)
            
            # Remove rows with blank or null asset_name
            df = df[df['asset_name'].notna() & (df['asset_name'] != '')]
            
            # Check if dataframe is empty, and if so, add a row with asset_name as None
            if df.empty:
                df = pd.DataFrame({'asset_name': [None], 'last_name': [last_name], 
                                'first_name': [first_name], 'state': [state], 
                                'year': [year], 'chamber': [house_senate]})
            else:
                df['last_name'] = last_name
                df['first_name'] = first_name
                df['state'] = state
                df['year'] = year
                df['chamber'] = house_senate

            dataframes.append(df)

    combined_df = pd.concat(dataframes, ignore_index=True)
    combined_df.to_csv('./final_datasets/final_asset_data.csv', index=False)

    summarised_df = identify_bitcoin_crypto_holdings(combined_df)
    summarised_df = include_source_data_links_summary_data(summarised_df)
    summarised_df = filter_to_most_recent_year_per_person(summarised_df)

    # annotate congress status (current/past) using current member list
    current_member_keys = get_current_member_keyset()
    summarised_df['congress_status'] = summarised_df.apply(
        lambda r: 'current' if (r['last_name'], r['first_name'], r['state'], r['chamber']) in current_member_keys else 'past',
        axis=1
    )

    summarised_df = summarised_df[['last_name', 'first_name', 'party', 'state', 'chamber', 'congress_status', 'owner', 'filing_year', 'link', 'triggered_terms', 'matched_asset_names']] # reorder columns
    summarised_df = summarised_df.sort_values(by=['owner', 'last_name', 'first_name'], ascending=[False, True, True])
    summarised_df.to_csv('./final_datasets/final_summary_data.csv', index=False)
    make_markdown_for_readMe(summarised_df.sort_values(['last_name','first_name']))

    print(f"\033[32m\nSaved Asset Data: 'final_datasets/final_asset_data.csv'\033[0m")
    print(f"\033[32mSaved Bitcoin/Crypto Summary: 'final_datasets/final_summary_data.csv'\033[0m")
    print(f"\033[32mSaved Markdown for ReadMe: 'final_datasets/final_summary_data.md'\033[0m\n")
    return combined_df

def identify_bitcoin_crypto_holdings(combined_df):
    # create columns to capture matched terms and asset names, handling non-string cases
    combined_df['triggered_terms'] = combined_df['asset_name'].apply(
        lambda x: ', '.join([term for term in bitcoin_crypto_terms if isinstance(x, str) and term.lower() in x.lower()])
    )
    combined_df['matched_asset_names'] = combined_df['asset_name'].apply(
        lambda x: x if isinstance(x, str) and any(term.lower() in x.lower() for term in bitcoin_crypto_terms) else ''
    )

    combined_df['owner'] = combined_df['triggered_terms'] != ''

    # exclude rows containing any false positives
    combined_df.loc[
        combined_df['asset_name'].str.contains('|'.join(bitcoin_crypto_terms_false_positives), case=False, na=False),
        ['owner', 'triggered_terms', 'matched_asset_names']
    ] = [False, '', '']

    def _dedupe_terms(series: pd.Series) -> str:
        collected_terms = []
        seen_terms = set()
        for value in series:
            if not isinstance(value, str) or not value.strip():
                continue
            tokens = [token.strip() for token in value.split(',') if token.strip()]
            for token in tokens:
                if token not in seen_terms:
                    seen_terms.add(token)
                    collected_terms.append(token)
        return ', '.join(collected_terms)

    def _dedupe_asset_names(series: pd.Series) -> str:
        seen_assets = set()
        ordered_assets = []
        for asset in series:
            if not isinstance(asset, str) or not asset.strip():
                continue
            if asset not in seen_assets:
                seen_assets.add(asset)
                ordered_assets.append(asset)
        return ', '.join(ordered_assets)

    holdings_summary = combined_df.groupby(['last_name', 'first_name', 'state', 'chamber']).agg(
        owner=('owner', 'max'),
        triggered_terms=('triggered_terms', _dedupe_terms),
        matched_asset_names=('matched_asset_names', _dedupe_asset_names)
    ).reset_index()

    holdings_summary = holdings_summary.sort_values(by=['owner', 'last_name', 'first_name'], ascending=[False, True, True])
    
    return holdings_summary

def include_source_data_links_summary_data(data):
    csv_file_path = os.path.join(source_data_dir, "source_data_links.csv")
    if not os.path.isfile(csv_file_path):
        print(f"No file found at {csv_file_path}")
        return data

    source_data_links = pd.read_csv(csv_file_path)
    merged_data = pd.merge(
        data,
        source_data_links,
        how="left",
        on=["last_name", "first_name", "state"]
    )

    return merged_data

def filter_to_most_recent_year_per_person(data):
    if data is None or data.empty or 'filing_year' not in data.columns:
        return data
    df = data.copy()
    df['filing_year_num'] = pd.to_numeric(df['filing_year'], errors='coerce')
    df = df.sort_values(['last_name', 'first_name', 'state', 'filing_year_num'], ascending=[True, True, True, False])
    df = df.drop_duplicates(subset=['last_name', 'first_name', 'state'], keep='first')
    df = df.drop(columns=['filing_year_num'])
    return df

def get_current_member_keyset():
    try:
        members = get_congress_members(ignore_cache=False)
        keys = set()
        for member in members:
            name = member[0]
            parts = name.split(',')
            last_name = parts[0].strip()
            first_name = parts[1].strip() if len(parts) > 1 else ''
            state = member[2]
            chamber = member[3].lower()
            keys.add((last_name, first_name, state, chamber))
        return keys
    except BaseException as e:
        print(f"Warning: could not load current congress members ({e}). Defaulting all to 'past'.")
        return set()

def make_markdown_for_readMe(summarised_df):
    summarised_df["Name"] = summarised_df["last_name"] + ", " + summarised_df["first_name"]
    summarised_df["Party"] = summarised_df["party"]
    summarised_df["House"] = summarised_df["chamber"].str.title()
    summarised_df["Congress"] = summarised_df["congress_status"]
    summarised_df["Owner"] = summarised_df["owner"].apply(lambda x: "YES" if x else "NO")
    summarised_df["Disclosure"] = summarised_df.apply(
        lambda row: f"[{row['filing_year']}]({row['link']})" if row["link"] else "-", axis=1
    )
    summarised_df["Notes"] = summarised_df["matched_asset_names"].replace("", "-", regex=False)

    output_df = summarised_df[["Name", "Party", "state", "House", "Congress", "Owner", "Disclosure", "Notes"]]
    output_df = output_df.rename(columns={"state": "State"})

    markdown_content = "| Name | Party | State | House | Congress | Owner | Disclosure | Notes |\n"
    markdown_content += "|------|:-----:|:-----:|-------|:--------:|:------:|:----------:|-------|\n"
    for _, row in output_df.iterrows():
        markdown_content += f"| {row['Name']} | {row['Party']} | {row['State']} | {row['House']} | {row['Congress']} | {row['Owner']} | {row['Disclosure']} | {row['Notes']} |\n"

    with open("./final_datasets/final_summary_data.md", "w") as f:
        f.write(markdown_content)

if __name__ == '__main__':
    combined_df = combine_processed_data()