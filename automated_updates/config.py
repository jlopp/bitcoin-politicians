# search terms to identify holdings
bitcoin_crypto_terms = [
    # general terms
    'cryptocurrency',
    'blockchain',
    'crypto',
    'digital asset',
    'virtual currency',
    # bitcoin
    'btc', 
    'bitcoin', 
    # etfs
    'fbtc', 
    'ibit', 
    'arkb', 
    'bitb', 
    'grayscale', 
    'greyscale', 
    'gbtc', 
    'bito',
    # miners
    'argo blockchain',
    'arbk',
    'bitdeer',
    'btdr',
    'bitfarms',
    'bitf',
    'canaan',
    #'can', // too many false positives
    'cipher mining',
    'cifr',
    'cleanspark',
    'clsk',
    'hive digital technologies',
    '\(hive\)',
    'hut 8 mining',
    '\(hut\)',
    'iris energy',
    'iren',
    'marathon digital',
    '\(mara\)',
    'riot blockchain',
    '\(riot\)',
    'terawulf',
    'wulf',
    # bitcoin/crypto proxy companies
    'coinbase', 
    '\(coin\)',
    'core scientific',
    'corz',
    'galaxy digital',
    'glxy',
    'microstrategy', 
    'mstr',
    'semler scientific',
    'smlr',
    'block, Inc',
    'block inc',
    '\(sq\)',
    # shitcoins
    'ethereum',
    ' eth ',
    'litecoin', 
    'ltc',
    'ripple',
    'xrp',
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
    'Armstrong',
    'BTC LifePath',
    'H&R',
    'H & R',
    'Marathon Oil',
    'Marathon Petroleum',
    'Marriott',
    'Pershing',
    'Quonset',
    'Squibb',
    'CALIF PRSMULTCCN EGID COR',
    'XRPO Inc PC 360'
]

source_data_dir = './all_source_data/'
intermediate_files_dir = './intermediate_files/'
processed_data_dir = './all_processed_data/'

house_messy_pdf_dir = intermediate_files_dir + 'house_messy_intermediate_files/'
house_clean_pdf_dir = intermediate_files_dir + 'house_clean_intermediate_files/'
senate_dir = intermediate_files_dir + 'senate_intermediate_files/'