"""
Brain YAGATI v2 - Universe Builder CLI

Main entry point for generating the deterministic tradable universe.
Uses CoinGecko API to fetch top cryptocurrencies by market cap.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import requests


# Stablecoins to exclude from the universe
STABLECOINS = {
    "USDT", "USDC", "BUSD", "DAI", "TUSD", "USDD", "USDP", "GUSD", 
    "FRAX", "LUSD", "SUSD", "USDN", "USDX", "EURS", "EURT", "USTC", 
    "UST", "FEI", "HUSD", "CUSD", "OUSD", "ALUSD", "TRIBE", "RSV"
}


def fetch_coingecko_top_coins(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch top cryptocurrencies by market cap from CoinGecko API.
    
    Args:
        limit: Number of coins to fetch (default: 100)
    
    Returns:
        List of coin data dictionaries
    """
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": False
    }
    
    retries = 3
    delay = 5
    timeout = 30
    
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt + 1}/{retries - 1} after error: {e}")
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                raise


def build_universe() -> Dict[str, Any]:
    """
    Build the tradable universe from CoinGecko data.
    
    Returns:
        Dictionary with universe metadata and symbols
    """
    print("Fetching top 100 cryptocurrencies from CoinGecko...")
    coins = fetch_coingecko_top_coins(limit=100)
    
    print(f"Fetched {len(coins)} coins from CoinGecko")
    
    # Filter out stablecoins and generate USDT pairs
    symbols = []
    for coin in coins:
        symbol = coin["symbol"].upper()
        if symbol not in STABLECOINS:
            usdt_pair = f"{symbol}USDT"
            symbols.append(usdt_pair)
    
    print(f"Filtered to {len(symbols)} trading pairs (excluded {len(coins) - len(symbols)} stablecoins)")
    
    # Build universe structure
    universe = {
        "version": "1.0",
        "source": "coingecko",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "symbols": symbols
    }
    
    return universe


def main():
    """Main entry point for universe builder"""
    universe = build_universe()
    
    # Save to JSON file
    output_path = Path(__file__).parent / "universe.json"
    with open(output_path, "w") as f:
        json.dump(universe, f, indent=2)
    
    print(f"\n✅ Universe saved to: {output_path}")
    print(f"   Total symbols: {len(universe['symbols'])}")
    print(f"   Version: {universe['version']}")
    print(f"   Source: {universe['source']}")
    print(f"\nFirst 10 symbols:")
    for symbol in universe['symbols'][:10]:
        print(f"  - {symbol}")
    if len(universe['symbols']) > 10:
        print(f"  ... and {len(universe['symbols']) - 10} more")


if __name__ == "__main__":
    main()