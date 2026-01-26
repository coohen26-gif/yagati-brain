from brain_v2.universe.bitget_client import fetch_usdt_perpetual_markets

def main():
    """Main entry point for universe builder"""
    bitget_symbols = fetch_usdt_perpetual_markets()
    print(f"Fetched {len(bitget_symbols)} symbols from Bitget USDT Perpetual Futures")

if __name__ == "__main__":
    main()