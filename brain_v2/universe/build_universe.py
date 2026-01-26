"""
Brain YAGATI v2 - Universe Builder CLI

Main entry point for generating the deterministic tradable universe.
"""

from brain_v2.universe.bitget_client import fetch_usdt_perpetual_markets


def main():
    """Main entry point for universe builder"""
    print("Fetching USDT Perpetual Futures symbols from Bitget...")
    bitget_symbols = fetch_usdt_perpetual_markets()
    print(f"Fetched {len(bitget_symbols)} symbols")
    for symbol in bitget_symbols[:10]:  # Show first 10
        print(f"  - {symbol}")
    if len(bitget_symbols) > 10:
        print(f"  ... and {len(bitget_symbols) - 10} more")


if __name__ == "__main__":
    main()