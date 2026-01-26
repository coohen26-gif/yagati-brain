"""
Brain YAGATI v2 - Universe Builder Module

Deterministic tradable universe generator that:
- Fetches top 100 cryptocurrencies by market cap from CoinGecko
- Excludes stablecoins and stable-like assets
- Intersects with Bitget USDT Perpetual Futures markets
- Produces a canonical list of ≤50 symbols in Bitget format
- Writes output to a local JSON file
"""

__version__ = "1.0.0"
