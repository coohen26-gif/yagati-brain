import requests
import time
from typing import List


def fetch_usdt_perpetual_markets(base_url: str = "https://api.bitget.com") -> List[str]:
    """
    Fetch active USDT perpetual futures markets from the Bitget API.
    
    Args:
        base_url (str): The base URL for the Bitget API. Defaults to "https://api.bitget.com".
    
    Returns:
        List[str]: A list of normalized symbol strings.
    """
    endpoint = f"{base_url}/api/mix/v1/market/contracts"
    params = {"productType": "usdt-futures"}
    retries = 3
    delay = 5
    timeout = 30
    
    for attempt in range(retries):
        try:
            response = requests.get(endpoint, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            # Filter active contracts
            active_contracts = [contract for contract in data['data'] if contract['supportMarginCoins']]
            
            # Normalize symbols
            normalized_symbols = [normalize_bitget_symbol(contract['symbol']) for contract in active_contracts]
            
            # Only include symbols ending with USDT
            return [symbol for symbol in normalized_symbols if symbol.endswith("USDT")]
        except requests.exceptions.RequestException:
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                raise


def normalize_bitget_symbol(raw_symbol: str) -> str:
    """
    Normalize the Bitget symbol by removing the _UMCBL suffix.
    
    Args:
        raw_symbol (str): The raw symbol string from Bitget.
    
    Returns:
        str: The normalized symbol string.
    """
    return raw_symbol.replace("_UMCBL", "")