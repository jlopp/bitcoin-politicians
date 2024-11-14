# search terms to identify holdings
bitcoin_crypto_terms = [
    'btc', 
    'bitcoin', 
    'fbtc ', 
    'ibit ', 
    'ethereum', 
    'grayscale', 
    'greyscale', 
    'gbtc', 
    'arkb', 
    'bitb', 
    'coinbase', 
    'microstrategy', 
    'mstr ',
    'cryptocurrency',
    'bito ',
]

# terms to be explicitly excluded
bitcoin_crypto_terms_false_positives = [
    'BTC LifePath',
]

source_data_dir = './all_source_data_test/'
intermediate_files_dir = './intermediate_files_test/'
processed_data_dir = './all_processed_data_test/'

house_messy_pdf_dir = intermediate_files_dir + 'house_messy_intermediate_files/'
house_clean_pdf_dir = intermediate_files_dir + 'house_clean_intermediate_files/'
senate_dir = intermediate_files_dir + 'senate_intermediate_files/'