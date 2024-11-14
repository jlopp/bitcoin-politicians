# search terms to identify holdings
bitcoin_crypto_terms = [
    # general terms
    'cryptocurrency',
    'blockchain',
    # bitcoin
    'btc', 
    'bitcoin', 
    # etfs
    'fbtc ', 
    'ibit ', 
    'arkb', 
    'bitb', 
    'grayscale', 
    'greyscale', 
    'gbtc', 
    'bito ',
    # bitcoin/crypto proxy companies
    'coinbase', 
    'microstrategy', 
    'mstr ',
    'marathon digital',
    'riot blockchain',
    'cleanspark',
    'core scientific',
    'cipher mining',
    'hut 8 mining',
    'terawulf',
    # shitcoins
    'ethereum',
    'eth '
    'litecoin', 
    'ltc ',
    'ripple',
    'xrp ',
    'cardano',
    'polkadot',
    'chainlink',
    'dogecoin',
    'shiba inu',
    'solana', 
    'uniswap',
    'polygon',
]

# terms to be explicitly excluded
bitcoin_crypto_terms_false_positives = [
    'BTC LifePath',
]

source_data_dir = './all_source_data/'
intermediate_files_dir = './intermediate_files/'
processed_data_dir = './all_processed_data/'

house_messy_pdf_dir = intermediate_files_dir + 'house_messy_intermediate_files/'
house_clean_pdf_dir = intermediate_files_dir + 'house_clean_intermediate_files/'
senate_dir = intermediate_files_dir + 'senate_intermediate_files/'