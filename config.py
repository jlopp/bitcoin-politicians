import os 
from dotenv import load_dotenv

load_dotenv()

CRYPTO_ASSETS = {
    'assets': [
        {'type': 'token', 'name': 'Bitcoin', 'ticker': 'BTC'},
        {'type': 'token', 'name': 'Ethereum', 'ticker': 'ETH'},
        {'type': 'token', 'name': 'Solana', 'ticker': 'SOL'},
        {'type': 'token', 'name': 'BNB', 'ticker': 'BNB'},
        {'type': 'token', 'name': 'Dogecoin', 'ticker': 'DOGE'},
        {'type': 'token', 'name': 'XRP', 'ticker': 'XRP'},
        {'type': 'token', 'name': 'Cardano', 'ticker': 'ADA'},
        {'type': 'token', 'name': 'Tron', 'ticker': 'TRX'},
        {'type': 'token', 'name': 'Shiba Inu', 'ticker': 'SHIB'},
        {'type': 'token', 'name': 'Avalanche', 'ticker': 'AVAX'},
        {'type': 'token', 'name': 'Toncoin', 'ticker': 'TON'},
        {'type': 'token', 'name': 'Chainlink', 'ticker': 'LINK'},
        {'type': 'etf', 'name': 'iShares Bitcoin Trust ETF', 'ticker': 'IBIT'},
        {'type': 'etf', 'name': 'Grayscale Bitcoin Trust', 'ticker': 'GBTC'},
        {'type': 'etf', 'name': 'Grayscale Ethereum Trust', 'ticker': 'ETHE'},
        {'type': 'etf', 'name': 'ProShares Bitcoin Strategy ETF', 'ticker': 'BITO'},
        {'type': 'etf', 'name': 'ProShares Short Bitcoin Strategy ETF', 'ticker': 'BITI'},
        {'type': 'etf', 'name': 'Fidelity Wise Origin Bitcoin Fund', 'ticker': 'FBTC'},
        {'type': 'etf', 'name': 'ARK 21Shares Bitcoin ETF', 'ticker': 'ARKB'},
        {'type': 'etf', 'name': 'VanEck Digital Transformation ETF', 'ticker': 'DAPP'},
        {'type': 'etf', 'name': 'Invesco Alerian Galaxy Crypto Economy ETF', 'ticker': 'SATO'},
        {'type': 'etf', 'name': 'Fidelity Ethereum Fund ETF', 'ticker': 'FETH'},
        {'type': 'etf', 'name': 'ProShares Ether ETF', 'ticker': 'EETH'},
        {'type': 'token', 'name': 'Velodrome', 'ticker': 'Velo'}
    ]
}
