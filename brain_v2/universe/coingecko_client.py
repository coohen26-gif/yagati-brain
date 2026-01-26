"""
Brain YAGATI v2 - CoinGecko API Client

Fetches top cryptocurrencies by market cap from CoinGecko's public API.
"""

import requests
import time
from typing import List, Optional


class CoinGeckoClient:
    """Client for fetching cryptocurrency data from CoinGecko public API"""
    
    def __init__(
        self,
        base_url: str = "https://api.coingecko.com/api/v3",
        vs_currency: str = "usd",
        timeout: int = 30
    ):
        """
        Initialize CoinGecko client.
        
        Args:
            base_url: Base URL for CoinGecko API
            vs_currency: Currency for market cap ranking (default: "usd")
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip("/")
        self.vs_currency = vs_currency
        self.timeout = timeout
    
    def fetch_top_coins(
        self,
        top_n: int = 100,
        retry_count: int = 3,
        retry_delay: int = 5
    ) -> List[dict]:
        """
        Fetch top N cryptocurrencies by market cap.
        
        Args:
            top_n: Number of top coins to fetch (default: 100)
            retry_count: Number of retry attempts on failure (default: 3)
            retry_delay: Delay between retries in seconds (default: 5)
        
        Returns:
            List of coin dictionaries with keys: symbol, id, market_cap_rank, etc.
        
        Raises:
            Exception: If API call fails after all retries
        """
        endpoint = f"{self.base_url}/coins/markets"
        
        # Calculate pagination (CoinGecko max per_page is 250)
        per_page = min(top_n, 250)
        pages_needed = (top_n + per_page - 1) // per_page  # Ceiling division
        
        all_coins = []
        
        for page in range(1, pages_needed + 1):
            params = {
                "vs_currency": self.vs_currency,
                "order": "market_cap_desc",
                "per_page": per_page,
                "page": page,
                "sparkline": "false",
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
                    
                    coins = response.json()
                    all_coins.extend(coins)
                    
                    # Rate limiting: sleep between pages
                    if page < pages_needed:
                        time.sleep(1)
                    
                    break  # Success, exit retry loop
                    
                except (requests.exceptions.RequestException, Exception) as e:
                    if attempt < retry_count - 1:
                        # Exponential backoff
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"[WARN] CoinGecko API error (attempt {attempt + 1}/{retry_count}): {e}")
                        print(f"[INFO] Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        # Final attempt failed
                        raise Exception(
                            f"Failed to fetch CoinGecko data after {retry_count} attempts: {e}"
                        )
        
        # Trim to exact top_n if we fetched more
        return all_coins[:top_n]
    
    def ping(self) -> bool:
        """
        Check if CoinGecko API is reachable.
        
        Returns:
            True if API responds, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/ping",
                timeout=self.timeout
            )
            return response.status_code == 200
        except:
            return False
