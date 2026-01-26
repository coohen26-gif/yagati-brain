"""
Brain YAGATI v2 - Stablecoin Filters and Intersection Logic

Provides:
- Curated stablecoin denylist
- Intersection logic for CoinGecko and Bitget symbols
"""

from typing import List, Set

# Stablecoin denylist (case-insensitive)
STABLECOIN_DENYLIST = {
    # Major stablecoins
    "usdt", "tether", "tether-usdt",
    "usdc", "usd-coin",
    "dai", "dai-stablecoin",
    "tusd", "true-usd",
    "fdusd", "first-digital-usd",
    "usde", "ethena-usde",
    "frax", "frax-finance",
    "lusd", "liquity-usd",
    "pyusd", "paypal-usd",
    
    # Wrapped stablecoins
    "wusdc", "wrapped-usdc",
    "wusdt", "wrapped-usdt",
    
    # Additional stable-like assets
    "busd", "binance-usd",
    "gusd", "gemini-dollar",
    "usdp", "paxos-standard",
    "susd", "susd",
    "eurs", "stasis-eurs",
    "eurt", "tether-eurt",
    "usdn", "neutrino-usd",
    "usdj", "just-stablecoin",
    "usdx", "usdx",
    "tribe", "tribe-2",
    "fei", "fei-usd",
}


def is_stablecoin(symbol: str, coin_id: str = None) -> bool:
    """
    Check if a cryptocurrency is a stablecoin.
    
    Args:
        symbol: The symbol (e.g., "USDT", "BTC")
        coin_id: Optional CoinGecko ID (e.g., "tether", "bitcoin")
    
    Returns:
        True if the coin is a stablecoin, False otherwise
    """
    symbol_lower = symbol.lower()
    
    # Check symbol
    if symbol_lower in STABLECOIN_DENYLIST:
        return True
    
    # Check coin_id if provided
    if coin_id and coin_id.lower() in STABLECOIN_DENYLIST:
        return True
    
    return False


def filter_stablecoins(coins: List[dict]) -> List[dict]:
    """
    Filter out stablecoins from a list of coins.
    
    Args:
        coins: List of coin dictionaries with 'symbol' and optionally 'id' keys
    
    Returns:
        Filtered list without stablecoins
    """
    filtered = []
    for coin in coins:
        symbol = coin.get("symbol", "")
        coin_id = coin.get("id", "")
        
        if not is_stablecoin(symbol, coin_id):
            filtered.append(coin)
    
    return filtered


def normalize_symbol(symbol: str) -> str:
    """
    Normalize a symbol to uppercase and remove common suffixes.
    
    Args:
        symbol: The symbol to normalize
    
    Returns:
        Normalized symbol in uppercase
    """
    return symbol.upper()


def compute_intersection(
    coingecko_coins: List[dict],
    bitget_symbols: List[str],
    target_size: int = 50
) -> tuple[List[str], dict]:
    """
    Compute intersection of CoinGecko coins and Bitget symbols.
    
    Args:
        coingecko_coins: List of CoinGecko coin dicts (after stablecoin filtering)
        bitget_symbols: List of Bitget USDT symbols (e.g., ["BTCUSDT", "ETHUSDT"])
        target_size: Maximum number of symbols to return (default 50)
    
    Returns:
        Tuple of (symbols_list, metadata_dict)
        - symbols_list: List of Bitget format symbols (e.g., ["BTCUSDT", "ETHUSDT"])
        - metadata_dict: Counts and statistics
    """
    # Build set of Bitget base symbols for fast lookup
    # E.g., "BTCUSDT" -> "BTC"
    bitget_base_set = set()
    for symbol in bitget_symbols:
        if symbol.endswith("USDT"):
            base = symbol[:-4]  # Remove "USDT"
            bitget_base_set.add(base.upper())
    
    # Build mapping of CoinGecko symbols to full coin data (sorted by rank)
    coingecko_sorted = sorted(
        coingecko_coins,
        key=lambda x: x.get("market_cap_rank", float("inf"))
    )
    
    # Find intersection
    intersected_symbols = []
    for coin in coingecko_sorted:
        cg_symbol = coin.get("symbol", "").upper()
        
        # Check if this CoinGecko symbol exists in Bitget
        if cg_symbol in bitget_base_set:
            bitget_symbol = f"{cg_symbol}USDT"
            intersected_symbols.append(bitget_symbol)
            
            # Stop if we've reached target size
            if len(intersected_symbols) >= target_size:
                break
    
    # Build metadata
    metadata = {
        "coingecko_input_count": len(coingecko_coins),
        "bitget_perp_markets": len(bitget_symbols),
        "bitget_base_symbols": len(bitget_base_set),
        "intersection_count": len(intersected_symbols),
        "final_count": len(intersected_symbols),
    }
    
    return intersected_symbols, metadata


def symbol_mapping_override() -> dict:
    """
    Symbol mapping overrides for known mismatches between CoinGecko and Bitget.
    
    Returns:
        Dictionary mapping CoinGecko symbol -> Bitget symbol
    """
    # Currently no known mismatches, but this can be extended
    # Example: {"MIOTA": "IOTA", "WBTC": "BTC"}
    return {}
