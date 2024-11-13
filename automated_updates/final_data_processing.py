import os
import pandas as pd

def combine_processed_data():
    folder_path = 'all_processed_data'

    dataframes = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            parts = filename.split('_')
            name = parts[0]
            state = parts[1]
            year = parts[2]
            house_senate = parts[3].replace('.csv', '')

            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            
            df['name'] = name
            df['state'] = state
            df['year'] = year
            df['chamber'] = house_senate

            dataframes.append(df)

    combined_df = pd.concat(dataframes, ignore_index=True)
    combined_df.to_csv('./final_data/final_asset_data.csv', index=False)

    summarised_df = identify_bitcoin_crypto_holdings(combined_df)
    summarised_df.to_csv('./final_data/final_summary_data.csv', index=False)
    
    print(f"Files combined successfully into 'final_data/final_asset_data.csv'")
    print(f"Files summarised into 'final_data/final_summary_data.csv'")

    return combined_df

def identify_bitcoin_crypto_holdings(combined_df):
    from config import bitcoin_crypto_terms, bitcoin_crypto_terms_false_positives

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

if __name__ == '__main__':
    combined_df = combine_processed_data()