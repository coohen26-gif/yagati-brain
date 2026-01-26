"""
Market Universe Configuration

Defines the symbols to analyze.
Start with a small universe for MVP.
"""

# Top crypto assets for MVP (reduced to 5 for faster execution)
SYMBOL_UNIVERSE = [
    "BTCUSDT",   # Bitcoin
    "ETHUSDT",   # Ethereum
    "SOLUSDT",   # Solana
    "BNBUSDT",   # Binance Coin
    "XRPUSDT",   # Ripple
]

# Can be expanded to top 10, 25, or 50 later
SYMBOL_UNIVERSE_EXTENDED = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "DOGEUSDT",
    "DOTUSDT",
    "MATICUSDT",
]
