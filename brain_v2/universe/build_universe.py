"""
Brain YAGATI v2 - Universe Builder CLI

Main entry point for generating the deterministic tradable universe.

Usage:
    python3 -m brain_v2.universe.build_universe

Environment Variables:
    UNIVERSE_OUTPUT_PATH        - Output JSON path (default: /opt/yagati/data/universe_usdt_perp.json)
    COINGECKO_VS_CURRENCY      - CoinGecko currency (default: usd)
    COINGECKO_TOP_N            - Number of top coins to fetch (default: 100)
    BITGET_API_BASE_URL        - Bitget API base URL (default: https://api.bitget.com)
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from brain_v2.universe.coingecko_client import CoinGeckoClient
from brain_v2.universe.bitget_client import BitgetClient
from brain_v2.universe.filters import filter_stablecoins, compute_intersection


def get_env_config() -> dict:
    """Load configuration from environment variables with defaults"""
    return {
        "output_path": os.getenv(
            "UNIVERSE_OUTPUT_PATH",
            "/opt/yagati/data/universe_usdt_perp.json"
        ),
        "coingecko_vs_currency": os.getenv("COINGECKO_VS_CURRENCY", "usd"),
        "coingecko_top_n": int(os.getenv("COINGECKO_TOP_N", "100")),
        "bitget_api_base_url": os.getenv(
            "BITGET_API_BASE_URL",
            "https://api.bitget.com"
        ),
        "target_size": 50,  # Fixed target size as per spec
    }


def ensure_output_directory(output_path: str) -> None:
    """Ensure the output directory exists"""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)


def build_universe(config: dict = None) -> dict:
    """
    Build the deterministic tradable universe.
    
    Args:
        config: Optional configuration dict (uses env vars if None)
    
    Returns:
        Universe data dictionary
    
    Raises:
        Exception: If any step fails
    """
    if config is None:
        config = get_env_config()
    
    print("\n" + "="*60)
    print("Brain YAGATI v2 - Universe Builder")
    print("="*60 + "\n")
    
    # Step 1: Fetch from CoinGecko
    print(f"[INFO] Fetching top {config['coingecko_top_n']} cryptocurrencies from CoinGecko...")
    coingecko_client = CoinGeckoClient(
        vs_currency=config["coingecko_vs_currency"]
    )
    
    coingecko_coins = coingecko_client.fetch_top_coins(
        top_n=config["coingecko_top_n"]
    )
    print(f"[INFO] CoinGecko fetched: {len(coingecko_coins)} coins")
    
    # Step 2: Apply stablecoin filter
    print("[INFO] Applying stablecoin filter...")
    filtered_coins = filter_stablecoins(coingecko_coins)
    print(f"[INFO] After stable exclusion: {len(filtered_coins)} coins")
    excluded_count = len(coingecko_coins) - len(filtered_coins)
    if excluded_count > 0:
        print(f"[INFO] Excluded {excluded_count} stablecoins")
    
    # Step 3: Fetch Bitget USDT Perpetual markets
    print("[INFO] Fetching Bitget USDT Perpetual Futures markets...")
    bitget_client = BitgetClient(base_url=config["bitget_api_base_url"])
    bitget_symbols = bitget_client.fetch_usdt_perpetual_markets()
    print(f"[INFO] Bitget USDT Perp markets found: {len(bitget_symbols)}")
    
    # Step 4: Compute intersection
    print("[INFO] Computing intersection...")
    symbols, metadata = compute_intersection(
        coingecko_coins=filtered_coins,
        bitget_symbols=bitget_symbols,
        target_size=config["target_size"]
    )
    
    print(f"[INFO] Intersection count: {metadata['intersection_count']}")
    print(f"[INFO] Selecting top {config['target_size']} by market cap...")
    print(f"[INFO] Final universe size: {len(symbols)}")
    
    # Warning if less than target
    if len(symbols) < config["target_size"]:
        print(f"[WARN] Intersection yielded only {len(symbols)} symbols (target: {config['target_size']})")
        print(f"[WARN] Using all available symbols")
    
    # Step 5: Build output structure
    universe_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "market": "bitget_usdt_perp",
        "source": {
            "coingecko_top_n": config["coingecko_top_n"],
            "target_size": config["target_size"],
        },
        "symbols": symbols,
        "metadata": {
            "coingecko_fetched": len(coingecko_coins),
            "after_stable_exclusion": len(filtered_coins),
            "bitget_perp_markets": len(bitget_symbols),
            "intersection_count": metadata["intersection_count"],
            "final_count": len(symbols),
        }
    }
    
    return universe_data


def write_universe_json(universe_data: dict, output_path: str) -> None:
    """
    Write universe data to JSON file.
    
    Args:
        universe_data: Universe data dictionary
        output_path: Path to output JSON file
    
    Raises:
        Exception: If write fails
    """
    print(f"[INFO] Writing to {output_path}")
    
    try:
        ensure_output_directory(output_path)
        
        with open(output_path, "w") as f:
            json.dump(universe_data, f, indent=2)
        
        # Verify file was written
        if not os.path.exists(output_path):
            raise Exception(f"Failed to write output file: {output_path}")
        
        file_size = os.path.getsize(output_path)
        print(f"[INFO] Written {file_size} bytes to {output_path}")
        
    except Exception as e:
        raise Exception(f"Failed to write JSON to {output_path}: {e}")


def main():
    """Main CLI entry point"""
    try:
        # Load configuration
        config = get_env_config()
        
        # Build universe
        universe_data = build_universe(config)
        
        # Write to file
        write_universe_json(universe_data, config["output_path"])
        
        # Success
        print("\n" + "="*60)
        print("[SUCCESS] Universe generation complete!")
        print("="*60)
        print(f"\nGenerated {len(universe_data['symbols'])} symbols")
        print(f"Output: {config['output_path']}")
        print()
        
        return 0
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"[ERROR] Universe generation failed!")
        print("="*60)
        print(f"\nError: {e}")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
