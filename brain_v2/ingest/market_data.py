"""
Market Data Ingestion Module

Fetches real market data using existing Supabase API.
No fake data allowed.
"""

import requests
import time
from typing import List, Dict, Optional
from brain_v2.config.settings import SUPABASE_URL, SUPABASE_ANON_KEY, OHLC_LIMIT
from brain_v2.governance.logger import get_logger


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
        logger = get_logger()
        url = f"{self.base_url}/functions/v1/market-data/ohlc"
        params = {
            "symbol": symbol,
            "timeframe": timeframe,
            "limit": str(limit),
        }
        
        max_retries = 3
        base_delay = 1  # seconds
        
        for attempt in range(max_retries):
            # Throttle before each attempt (including retries)
            time.sleep(0.5)
            
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
                source = "SUPABASE_EDGE (upstream: CoinGecko)"
                
                # Discriminant logging
                if status_code == 429:
                    logger.warning(
                        f"Rate limit hit: {symbol} {timeframe} (attempt {attempt+1}/{max_retries})",
                        context={"source": source, "status_code": status_code}
                    )
                    should_retry = True
                elif 400 <= status_code < 500:
                    logger.error(
                        f"Client error ({status_code}): {symbol} {timeframe}",
                        context={"source": source, "status_code": status_code}
                    )
                    should_retry = False  # Don't retry 4xx (except 429)
                elif 500 <= status_code < 600:
                    logger.warning(
                        f"Server error ({status_code}): {symbol} {timeframe} (attempt {attempt+1}/{max_retries})",
                        context={"source": source, "status_code": status_code}
                    )
                    should_retry = True
                else:
                    logger.error(
                        f"HTTP error ({status_code}): {symbol} {timeframe}",
                        context={"source": source, "status_code": status_code}
                    )
                    should_retry = False
                
                # Retry logic
                if should_retry and attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"HTTP error ({status_code}) from {source} fetching {symbol} {timeframe}: {e}")
                    
            except requests.exceptions.Timeout as e:
                source = "SUPABASE_EDGE (upstream: CoinGecko)"
                logger.warning(
                    f"Timeout: {symbol} {timeframe} (attempt {attempt+1}/{max_retries})",
                    context={"source": source, "error": "timeout"}
                )
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Timeout from {source} fetching {symbol} {timeframe}: {e}")
                    
            except requests.exceptions.RequestException as e:
                source = "SUPABASE_EDGE (upstream: CoinGecko)"
                logger.warning(
                    f"Network error: {symbol} {timeframe} (attempt {attempt+1}/{max_retries})",
                    context={"source": source, "error": "network"}
                )
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Network error from {source} fetching {symbol} {timeframe}: {e}")
                    
            except Exception as e:
                source = "SUPABASE_EDGE (upstream: CoinGecko)"
                logger.error(
                    f"Unexpected error: {symbol} {timeframe}: {e}",
                    context={"source": source, "error_type": type(e).__name__}
                )
                raise Exception(f"Unexpected error from {source} fetching {symbol} {timeframe}: {e}")
    
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
        logger = get_logger()
        results = {}
        for tf in timeframes:
            try:
                results[tf] = self.fetch_ohlc(symbol, tf)
            except Exception as e:
                # Log error but continue with other timeframes
                logger.error(
                    f"Error fetching {symbol} {tf}: {e}",
                    context={"symbol": symbol, "timeframe": tf}
                )
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
    logger = get_logger()
    fetcher = MarketDataFetcher()
    try:
        return fetcher.fetch_ohlc(symbol, timeframe)
    except Exception as e:
        logger.error(
            f"Market data fetch failed: {e}",
            context={"symbol": symbol, "timeframe": timeframe}
        )
        return None
