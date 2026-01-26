"""
Market Data Ingestion Module

Fetches real market data using existing Supabase API.
No fake data allowed.
"""

import requests
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
        }
    
    def fetch_ohlc(
        self, 
        symbol: str, 
        timeframe: str, 
        limit: int = OHLC_LIMIT
    ) -> Optional[List[Dict]]:
        """
        Fetch OHLC candle data for a symbol.
        
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
        
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params, 
                timeout=20
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error fetching {symbol} {timeframe}: {e}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request error fetching {symbol} {timeframe}: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error fetching {symbol} {timeframe}: {e}")
    
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
