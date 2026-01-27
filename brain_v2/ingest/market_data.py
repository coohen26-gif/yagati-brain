"""
Market Data Ingestion Module

Fetches real market data using existing Supabase API.
No fake data allowed.
"""

import requests
import time
from typing import List, Dict, Optional
from brain_v2.config.settings import SUPABASE_URL, SUPABASE_ANON_KEY, OHLC_LIMIT


class MarketDataFetcher:
    """Fetches market data from Supabase edge function"""
    
    def __init__(self):
        """Initialize market data fetcher"""
        self.base_url = SUPABASE_URL
        self.headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "YAGATI-Brain/2.0 (Market Analysis Bot)",
        }
    
    def fetch_ohlc(
        self, 
        symbol: str, 
        timeframe: str, 
        limit: int = OHLC_LIMIT
    ) -> Optional[List[Dict]]:
        """
        Fetch OHLC candle data for a symbol with retry logic, throttling, and explicit error handling.
        
        Args:
            symbol: Market symbol (e.g., "BTCUSDT")
            timeframe: Timeframe (e.g., "1h", "4h", "1d")
            limit: Number of candles to fetch
            
        Returns:
            List of OHLC candles or None if error
            
        Raises:
            Exception: On API error (to be caught and logged by caller)
        """
        url = f"{self.base_url}/functions/v1/market-data/ohlc"
        params = {
            "symbol": symbol,
            "timeframe": timeframe,
            "limit": str(limit),
        }
        
        max_retries = 3
        base_delay = 1  # seconds
        
        # Throttle before request
        time.sleep(0.5)
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    params=params, 
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                
                # Discriminant logging
                if status_code == 429:
                    print(f"⚠️ Rate limit hit: {symbol} {timeframe} (attempt {attempt+1}/{max_retries})")
                    should_retry = True
                elif 400 <= status_code < 500:
                    print(f"❌ Client error ({status_code}): {symbol} {timeframe}")
                    should_retry = False  # Don't retry 4xx (except 429)
                elif 500 <= status_code < 600:
                    print(f"⚠️ Server error ({status_code}): {symbol} {timeframe} (attempt {attempt+1}/{max_retries})")
                    should_retry = True
                else:
                    print(f"❌ HTTP error ({status_code}): {symbol} {timeframe}")
                    should_retry = False
                
                # Retry logic
                if should_retry and attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"   Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"HTTP error ({status_code}) fetching {symbol} {timeframe}: {e}")
                    
            except requests.exceptions.Timeout as e:
                print(f"⚠️ Timeout: {symbol} {timeframe} (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    print(f"   Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Timeout fetching {symbol} {timeframe}: {e}")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Network error: {symbol} {timeframe} (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    print(f"   Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Network error fetching {symbol} {timeframe}: {e}")
                    
            except Exception as e:
                print(f"❌ Unexpected error: {symbol} {timeframe}: {e}")
                raise Exception(f"Unexpected error fetching {symbol} {timeframe}: {e}")
        
        # Should never reach here
        raise Exception(f"Failed to fetch {symbol} {timeframe} after {max_retries} attempts")
    
    def fetch_multiple_timeframes(
        self, 
        symbol: str, 
        timeframes: List[str]
    ) -> Dict[str, Optional[List[Dict]]]:
        """
        Fetch OHLC data for multiple timeframes.
        
        Args:
            symbol: Market symbol
            timeframes: List of timeframes
            
        Returns:
            Dict mapping timeframe to OHLC data (or None if error)
        """
        results = {}
        for tf in timeframes:
            try:
                results[tf] = self.fetch_ohlc(symbol, tf)
            except Exception as e:
                # Log error but continue with other timeframes
                print(f"⚠️ Error fetching {symbol} {tf}: {e}")
                results[tf] = None
        return results


def fetch_market_data(symbol: str, timeframe: str) -> Optional[List[Dict]]:
    """
    Convenience function to fetch market data.
    
    Args:
        symbol: Market symbol
        timeframe: Timeframe
        
    Returns:
        OHLC candles or None if error
    """
    fetcher = MarketDataFetcher()
    try:
        return fetcher.fetch_ohlc(symbol, timeframe)
    except Exception as e:
        print(f"⚠️ Market data fetch failed: {e}")
        return None
