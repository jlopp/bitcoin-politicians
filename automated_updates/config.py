# download chromedriver from https://googlechromelabs.github.io/chrome-for-testing/, path to executable here
chrome_driver_path = ''

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