# Part 3 of the pipeline: 
# Identifies bitcoin/crypto assets and combines files in all_processed_data into final dataframes

import os
import pandas as pd
from config import processed_data_dir, source_data_dir
from config import bitcoin_crypto_terms, bitcoin_crypto_terms_false_positives

def combine_processed_data():
    dataframes = []

    for filename in os.listdir(processed_data_dir):
        if filename.endswith('.csv'):
            parts = filename.split('_')
            name = parts[0]
            state = parts[1]
            year = parts[2]
            house_senate = parts[3].replace('.csv', '')

            file_path = os.path.join(processed_data_dir, filename)
            df = pd.read_csv(file_path)
            
            # Remove rows with blank or null asset_name
            df = df[df['asset_name'].notna() & (df['asset_name'] != '')]
            
            df['name'] = name
            df['state'] = state
            df['year'] = year
            df['chamber'] = house_senate

            dataframes.append(df)

    combined_df = pd.concat(dataframes, ignore_index=True)
    combined_df.to_csv('./final_datasets/final_asset_data.csv', index=False)

    summarised_df = identify_bitcoin_crypto_holdings(combined_df)
    summarised_df = include_source_data_links_summary_data(summarised_df)
    summarised_df.to_csv('./final_datasets/final_summary_data.csv', index=False)

    print(f"\033[32m\nSaved Asset Data: 'final_datasets/final_asset_data.csv'\033[0m")
    print(f"\033[32mSaved Bitcoin/Crypto Summary: 'final_datasets/final_summary_data.csv'\033[0m\n")
    return combined_df

def identify_bitcoin_crypto_holdings(combined_df):
    # create columns to capture matched terms and asset names, handling non-string cases
    combined_df['triggered_terms'] = combined_df['asset_name'].apply(
        lambda x: ', '.join([term for term in bitcoin_crypto_terms if isinstance(x, str) and term.lower() in x.lower()])
    )
    combined_df['matched_asset_names'] = combined_df['asset_name'].apply(
        lambda x: x if isinstance(x, str) and any(term.lower() in x.lower() for term in bitcoin_crypto_terms) else ''
    )

    combined_df['bitcoin_crypto'] = combined_df['triggered_terms'] != ''

    # exclude rows containing any false positives
    combined_df.loc[
        combined_df['asset_name'].str.contains('|'.join(bitcoin_crypto_terms_false_positives), case=False, na=False),
        ['bitcoin_crypto', 'triggered_terms', 'matched_asset_names']
    ] = [False, '', '']

    holdings_summary = combined_df.groupby(['name', 'state', 'chamber']).agg(
        bitcoin_crypto=('bitcoin_crypto', 'max'),
        triggered_terms=('triggered_terms', lambda x: ', '.join(set(filter(None, x)))),
        matched_asset_names=('matched_asset_names', lambda x: ', '.join(set(filter(None, x))))
    ).reset_index()

    holdings_summary = holdings_summary.sort_values(by=['bitcoin_crypto', 'name'], ascending=[False, True])
    
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
        on=["name", "state"]
    )

    return merged_data

if __name__ == '__main__':
    combined_df = combine_processed_data()