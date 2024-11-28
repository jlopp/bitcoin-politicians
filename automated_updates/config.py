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
    # bitcoin etfs
    # 'arka', # too many false positives
    'arkb',
    'bitb',
    'bitc',
    'bito',
    'biti',
    'bitu',
    'bitx',
    'brrr',
    'btco',
    'btcw', 
    #'defi', # too many false positives
    'ezbc',
    'fbtc',
    'grayscale',
    'greyscale',
    'gbtc',
    'hodl',
    'ibit',
    'sbit',
    # ethereum etfs
    'aeth',
    'arky',
    'arkz',
    'ceth',
    'eeth',
    # 'etha', # too many false positives
    'ethd',
    # 'ethe', # too many false positives
    'etht',
    'ethu',
    'ethv',
    'feth',
    # 'seth', # too many false positives
    # mixed crypto etfs
    # 'bete', # too many false positives
    # 'beth', # too many false positives
    'bitq',
    'bits',
    'bitw',
    'blkc',  
    # 'btf', # too many false positives
    'btop',
    'dapp',
    # 'sato', # too many false positives
    'spbc',
    'stce',
    # miners
    'argo blockchain',
    'arbk',
    'bitdeer',
    'btdr',
    'bitfarms',
    'bitf',
    'canaan',
    '\(can\)',
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
    'wgmi',
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
    'block, inc',
    'block inc',
    '\(sq\)',
    # shitcoins
    'avalanche',
    # 'avax', # too many false positives
    'binance',
    # 'bch', # too many false positives
    'cardano',
    'chainlink',
    'dogecoin',
    'ethereum',
    ' eth ',
    'litecoin', 
    'ltc',
    'monero',
    'xmr',
    'polkadot',
    'polygon',
    'ripple',
    'xrp',
    'shiba inu',
    'solana',
    'toncoin',
    'uniswap',
]

# terms to be explicitly excluded
bitcoin_crypto_terms_false_positives = [
    'Armstrong',
    'BTC LifePath',
    'H&R',
    'H & R',
    'Healtcare',
    'Marathon Oil',
    'Marathon Petroleum',
    'Marriott',
    'Pershing',
    'Quonset',
    'Squibb',
    'CALIF PRSMULTCCN EGID COR',
    'XRPO Inc PC 360',
    'Canaan LLC',
]

source_data_dir = './all_source_data/'
intermediate_files_dir = './intermediate_files/'
processed_data_dir = './all_processed_data/'

house_messy_pdf_dir = intermediate_files_dir + 'house_messy_intermediate_files/'
house_clean_pdf_dir = intermediate_files_dir + 'house_clean_intermediate_files/'
senate_dir = intermediate_files_dir + 'senate_intermediate_files/'