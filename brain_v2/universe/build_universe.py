# Updated build_universe.py

# Import statements
from brain_v2.universe.bitget_client import fetch_usdt_perpetual_markets

# Other parts of the code remain unchanged...

# Update the section instantiating the bitget_client
# Removed the BitgetClient instantiation
# bitget_client = BitgetClient(base_url=config["bitget_api_base_url"])
# Removed method call
# bitget_symbols = bitget_client.fetch_usdt_perpetual_markets()

# Updated the call to use the functional API directly
bitget_symbols = fetch_usdt_perpetual_markets(base_url=config["bitget_api_base_url"])

# Continue with the rest of the code...