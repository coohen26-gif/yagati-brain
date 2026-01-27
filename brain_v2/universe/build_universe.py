"""
Brain YAGATI v2 - Universe Builder CLI

Main entry point for generating the deterministic tradable universe.
Uses CoinGecko API to fetch top cryptocurrencies by market cap.
"""

import json
import os
import requests
import time
from datetime import datetime
from typing import List, Dict


# Known stablecoins to exclude from universe
STABLECOINS = {
    "USDT", "USDC", "BUSD", "DAI", "TUSD", "USDD", "USDP", "GUSD", "FRAX",
    "LUSD", "FEI", "TRIBE", "USTC", "UST", "HUSD", "sUSD", "EURS", "EURT",
    "CUSD", "XSGD", "ZUSD", "DUSD", "OUSD", "MIM"
}

def fetch_coingecko_top_coins(limit: int = 100) -> List[Dict]:
    """
    Fetch top cryptocurrencies by market cap from CoinGecko.
    
    Args:
        limit: Number of top coins to fetch (default: 100)
    
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
    
    for attempt in range(retries):
        try:
            print(f"Fetching top {limit} coins from CoinGecko...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"✓ Successfully fetched {len(data)} coins from CoinGecko")
            return data
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                wait_time = delay * (2 ** attempt)
                print(f"✗ Request failed: {e}")
                print(f"  Retrying in {wait_time} seconds... (attempt {attempt + 1}/{retries})")
                time.sleep(wait_time)
            else:
                print(f"✗ Failed after {retries} attempts")
                raise


def filter_stablecoins(coins: List[Dict]) -> List[str]:
    """
    Filter out stablecoins and return list of symbols.
    
    Args:
        coins: List of coin data from CoinGecko
    
    Returns:
        List of filtered symbols (uppercase)
    """
    filtered = []
    excluded = []
    
    for coin in coins:
        symbol = coin.get("symbol", "").upper()
        if symbol in STABLECOINS:
            excluded.append(symbol)
        else:
            filtered.append(symbol)
    
    print(f"✓ Filtered out {len(excluded)} stablecoins: {', '.join(sorted(excluded))}")
    print(f"✓ Kept {len(filtered)} trading symbols")
    
    return filtered

def generate_usdt_pairs(symbols: List[str]) -> List[str]:
    """
    Generate USDT trading pairs from symbol list.
    
    Args:
        symbols: List of base symbols
    
    Returns:
        List of USDT trading pairs (e.g., BTCUSDT, ETHUSDT)
    """
    pairs = [f"{symbol}USDT" for symbol in symbols]
    print(f"✓ Generated {len(pairs)} USDT trading pairs")
    return pairs

def save_universe(pairs: List[str], output_path: str) -> None:
    """
    Save universe to JSON file.
    
    Args:
        pairs: List of trading pairs
        output_path: Path to output JSON file
    """
    universe_data = {
        "version": "1.0",
        "source": "coingecko",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(pairs),
        "symbols": sorted(pairs)
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(universe_data, f, indent=2)
    
    print(f"✓ Universe saved to {output_path}")

def main():
    """Main entry point for universe builder"""
    print("=" * 60)
    print("YAGATI Brain V2 - Universe Builder")
    print("=" * 60)
    
    try:
        # Fetch top coins from CoinGecko
        coins = fetch_coingecko_top_coins(limit=100)
        
        # Filter out stablecoins
        symbols = filter_stablecoins(coins)
        
        # Generate USDT pairs
        pairs = generate_usdt_pairs(symbols)
        
        # Save to universe.json
        output_path = os.path.join(
            os.path.dirname(__file__),
            "universe.json"
        )
        save_universe(pairs, output_path)
        
        print("=" * 60)
        print(f"✓ Universe build complete!")
        print(f"  Total symbols: {len(pairs)}")
        print(f"  First 10: {', '.join(pairs[:10])}")
        if len(pairs) > 10:
            print(f"  ... and {len(pairs) - 10} more")
        print("=" * 60)
        
    except Exception as e:
        print("=" * 60)
        print(f"✗ Universe build failed: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()