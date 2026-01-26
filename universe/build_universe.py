from brain_v2.universe.bitget_client import fetch_usdt_perpetual_markets

def main():
    bitget_symbols = fetch_usdt_perpetual_markets()
    # Rest of the logic here
    print(f"Fetched {len(bitget_symbols)} symbols from Bitget USDT Perpetual Futures")

if __name__ == "__main__":
    main()