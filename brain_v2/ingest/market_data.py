"""
Market Data Ingestion Module

Fetches REAL OHLC data using CoinGecko /ohlc endpoint.
No fake data allowed. No reconstruction allowed.

Data Quality: NATIVE OHLC from CoinGecko (not derived/approximate)
"""

import json
import os
import requests
import time
from typing import List, Dict, Optional
from brain_v2.config.settings import OHLC_LIMIT
from brain_v2.governance.logger import get_logger


# Rate limiting configuration
MAX_API_CALLS_PER_CYCLE = 100  # Maximum API calls per analysis cycle


def load_symbol_mapping() -> Dict[str, str]:
    """
    Load symbol to CoinGecko ID mapping from JSON file.
    
    Returns:
        Dictionary mapping trading symbols to CoinGecko IDs
    
    Raises:
        FileNotFoundError: If mapping file doesn't exist
        ValueError: If mapping file is invalid
    """
    mapping_file = os.path.join(
        os.path.dirname(__file__),
        "symbol_mapping.json"
    )
    
    if not os.path.exists(mapping_file):
        raise FileNotFoundError(
            f"Symbol mapping file not found: {mapping_file}. "
            "This file is required for CoinGecko API integration."
        )
    
    try:
        with open(mapping_file, "r") as f:
            data = json.load(f)
        
        mappings = data.get("mappings", {})
        if not mappings:
            raise ValueError("Symbol mapping file contains no mappings")
        
        return mappings
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in symbol mapping file: {e}")
    except Exception as e:
        raise ValueError(f"Error loading symbol mapping: {e}")


class MarketDataFetcher:
    """Fetches NATIVE OHLC data from CoinGecko /ohlc endpoint"""
    
    def __init__(self):
        """Initialize CoinGecko fetcher with native OHLC support"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.headers = {
            "User-Agent": "YAGATI-Brain/2.0 (Market Analysis Bot)",
            "Accept": "application/json",
        }
        # Load symbol mapping dynamically
        self.symbol_mapping = load_symbol_mapping()
        self.api_call_count = 0  # Track API calls in current cycle
        
        logger = get_logger()
        logger.info(
            f"MarketDataFetcher initialized with {len(self.symbol_mapping)} symbol mappings",
            context={"data_quality": "NATIVE_OHLC", "source": "CoinGecko /ohlc endpoint"}
        )
    
    def reset_api_call_count(self):
        """Reset API call counter for new cycle"""
        self.api_call_count = 0
    
    def check_rate_limit(self, estimated_calls: int = 1) -> bool:
        """
        Check if we're within rate limit for this cycle.
        
        Args:
            estimated_calls: Number of calls about to be made
            
        Returns:
            True if within limit, False otherwise
        """
        logger = get_logger()
        
        if self.api_call_count + estimated_calls > MAX_API_CALLS_PER_CYCLE:
            logger.warning(
                f"API call limit exceeded: {self.api_call_count} + {estimated_calls} > {MAX_API_CALLS_PER_CYCLE}",
                context={"max_calls": MAX_API_CALLS_PER_CYCLE, "current": self.api_call_count}
            )
            return False
        
        return True
    
    def _get_coin_id(self, symbol: str) -> str:
        """
        Get CoinGecko coin ID from trading symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            
        Returns:
            CoinGecko coin ID
            
        Raises:
            ValueError: If symbol not in mapping
        """
        if symbol not in self.symbol_mapping:
            raise ValueError(
                f"Symbol {symbol} not in CoinGecko mapping. "
                f"Available symbols: {', '.join(sorted(self.symbol_mapping.keys()))}"
            )
        return self.symbol_mapping[symbol]
    
    def _map_timeframe_to_days(self, timeframe: str) -> int:
        """
        Map timeframe to CoinGecko /ohlc days parameter.
        
        CoinGecko /ohlc endpoint supports specific day ranges.
        
        Args:
            timeframe: Timeframe string (e.g., "1h", "4h", "1d")
            
        Returns:
            Days parameter for CoinGecko API
        """
        # CoinGecko /ohlc endpoint behavior:
        # - days=1: returns 4-hour candles for last 1-2 days
        # - days=7-90: returns 4-hour candles
        # - days>90: returns daily candles
        
        if timeframe == "1h":
            # For 1h data, we need recent 4h candles (closest available)
            return 1
        elif timeframe == "4h":
            # 4h candles available for 1-90 days
            return 7
        elif timeframe == "1d":
            # Daily candles available for days>90
            return 180
        else:
            # Default to 7 days
            return 7
    
    def fetch_ohlc(
        self, 
        symbol: str, 
        timeframe: str, 
        limit: int = OHLC_LIMIT
    ) -> Optional[List[Dict]]:
        """
        Fetch NATIVE OHLC candle data from CoinGecko /ohlc endpoint.
        
        DATA QUALITY: NATIVE OHLC (not reconstructed/approximate)
        
        Args:
            symbol: Market symbol (e.g., "BTCUSDT")
            timeframe: Timeframe (e.g., "1h", "4h", "1d")
            limit: Number of candles to fetch
            
        Returns:
            List of NATIVE OHLC candles or None if error
            
        Raises:
            Exception: On API error (to be caught and logged by caller)
        """
        logger = get_logger()
        
        # Check rate limit before making call
        if not self.check_rate_limit(estimated_calls=1):
            raise Exception(
                f"API call limit exceeded ({MAX_API_CALLS_PER_CYCLE} calls per cycle). "
                "Aborting to prevent rate limit issues."
            )
        
        max_retries = 3
        base_delay = 1  # seconds
        
        try:
            # Get CoinGecko ID
            coin_id = self._get_coin_id(symbol)
            
            # Calculate days parameter
            days = self._map_timeframe_to_days(timeframe)
            
            # Build URL - using NATIVE /ohlc endpoint
            url = f"{self.base_url}/coins/{coin_id}/ohlc"
            params = {
                "vs_currency": "usd",
                "days": days,
            }
            
            logger.info(
                f"Fetching NATIVE OHLC for {symbol} {timeframe} from CoinGecko",
                context={
                    "endpoint": "/ohlc",
                    "data_quality": "NATIVE_OHLC",
                    "coin_id": coin_id,
                    "days": days
                }
            )
            
            # Retry loop
            for attempt in range(max_retries):
                # Rate limiting: 2s between requests (30 calls/min)
                # Delay before each API call to respect CoinGecko rate limits
                time.sleep(2.0)
                
                try:
                    response = requests.get(url, headers=self.headers, params=params, timeout=30)
                    response.raise_for_status()
                    
                    # Increment API call counter
                    self.api_call_count += 1
                    
                    # Parse NATIVE OHLC response
                    # CoinGecko /ohlc returns: [[timestamp_ms, open, high, low, close], ...]
                    ohlc_raw = response.json()
                    
                    if not ohlc_raw:
                        raise Exception(f"No OHLC data returned for {symbol} {timeframe}")
                    
                    # Convert to our format
                    # NOTE: CoinGecko /ohlc endpoint does NOT provide volume data
                    # Volume is set to 0 as a placeholder for API compatibility
                    ohlc = []
                    for candle in ohlc_raw:
                        if len(candle) >= 5:
                            ohlc.append({
                                "timestamp": candle[0] // 1000,  # Convert ms to seconds
                                "open": float(candle[1]),
                                "high": float(candle[2]),
                                "low": float(candle[3]),
                                "close": float(candle[4]),
                                "volume": 0,  # /ohlc endpoint doesn't provide volume
                            })
                    
                    # Return most recent `limit` candles
                    ohlc = ohlc[-limit:]
                    
                    logger.info(
                        f"✓ Fetched {len(ohlc)} NATIVE OHLC candles for {symbol} {timeframe}",
                        context={
                            "data_quality": "NATIVE_OHLC",
                            "source": "CoinGecko /ohlc",
                            "api_calls_used": self.api_call_count
                        }
                    )
                    return ohlc
                    
                except requests.exceptions.HTTPError as e:
                    status_code = e.response.status_code
                    source = "CoinGecko /ohlc"
                    
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
                    source = "CoinGecko /ohlc"
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
                    source = "CoinGecko /ohlc"
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
            
        except ValueError as e:
            # Symbol not in mapping - log but don't crash entire cycle
            logger.error(f"Symbol mapping error: {e}", context={"symbol": symbol})
            raise Exception(f"Symbol mapping error: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error: {symbol} {timeframe}: {e}",
                context={"source": "CoinGecko /ohlc", "error_type": type(e).__name__}
            )
            raise Exception(f"Unexpected error from CoinGecko /ohlc fetching {symbol} {timeframe}: {e}")
    
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
