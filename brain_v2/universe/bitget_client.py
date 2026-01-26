"""
Brain YAGATI v2 - Bitget API Client

Fetches USDT Perpetual Futures markets from Bitget's public API.
"""

import requests
import time
from typing import List


class BitgetClient:
    """Client for fetching USDT Perpetual Futures markets from Bitget public API"""
    
    def __init__(
        self,
        base_url: str = "https://api.bitget.com",
        timeout: int = 30
    ):
        """
        Initialize Bitget client.
        
        Args:
            base_url: Base URL for Bitget API
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    
    def fetch_usdt_perpetual_markets(
        self,
        retry_count: int = 3,
        retry_delay: int = 5
    ) -> List[str]:
        """
        Fetch all active USDT Perpetual Futures markets.
        
        Args:
            retry_count: Number of retry attempts on failure (default: 3)
            retry_delay: Delay between retries in seconds (default: 5)
        
        Returns:
            List of symbols in Bitget format (e.g., ["BTCUSDT", "ETHUSDT"])
        
        Raises:
            Exception: If API call fails after all retries
        """
        # Bitget API endpoint for USDT-margined perpetual futures
        # productType: umcbl = USDT-margined perpetual
        endpoint = f"{self.base_url}/api/mix/v1/market/contracts"
        params = {
            "productType": "umcbl"
        }
        
        # Retry logic with exponential backoff
        for attempt in range(retry_count):
            try:
                response = requests.get(
                    endpoint,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Check if response has expected structure
                if "data" not in data:
                    raise Exception(f"Unexpected Bitget API response: missing 'data' key")
                
                contracts = data["data"]
                
                # Extract and normalize symbols
                symbols = []
                for contract in contracts:
                    # Skip if not active/online
                    if contract.get("supportMarginCoins") is None:
                        continue
                    
                    raw_symbol = contract.get("symbol", "")
                    if raw_symbol:
                        # Normalize: "BTCUSDT_UMCBL" -> "BTCUSDT"
                        normalized = self.normalize_bitget_symbol(raw_symbol)
                        
                        # Only include USDT pairs
                        if normalized.endswith("USDT"):
                            symbols.append(normalized)
                
                return symbols
                
            except (requests.exceptions.RequestException, Exception) as e:
                if attempt < retry_count - 1:
                    # Exponential backoff
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"[WARN] Bitget API error (attempt {attempt + 1}/{retry_count}): {e}")
                    print(f"[INFO] Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    raise Exception(
                        f"Failed to fetch Bitget data after {retry_count} attempts: {e}"
                    )
        
        return []
    
    @staticmethod
    def normalize_bitget_symbol(raw_symbol: str) -> str:
        """
        Convert Bitget symbol format to standard USDT format.
        
        Examples:
            "BTCUSDT_UMCBL" -> "BTCUSDT"
            "ETHUSDT" -> "ETHUSDT"
        
        Args:
            raw_symbol: Raw symbol from Bitget API
        
        Returns:
            Normalized symbol
        """
        # Remove product type suffix if present
        if "_" in raw_symbol:
            return raw_symbol.split("_")[0]
        return raw_symbol
    
    def ping(self) -> bool:
        """
        Check if Bitget API is reachable.
        
        Returns:
            True if API responds, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/mix/v1/market/contracts",
                params={"productType": "umcbl"},
                timeout=self.timeout
            )
            return response.status_code == 200
        except:
            return False
