"""
Market Data Ingestion Module

Fetches real market data using CoinGecko API.
No fake data allowed.
"""

import requests
import time
from typing import List, Dict, Optional
from brain_v2.config.settings import OHLC_LIMIT
from brain_v2.governance.logger import get_logger


# Deterministic symbol mapping: USDT pairs → CoinGecko IDs
SYMBOL_TO_COINGECKO_ID = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum",
    "BNBUSDT": "binancecoin",
    "XRPUSDT": "ripple",
    "ADAUSDT": "cardano",
    "DOGEUSDT": "dogecoin",
    "SOLUSDT": "solana",
    "DOTUSDT": "polkadot",
    "MATICUSDT": "matic-network",
    "LINKUSDT": "chainlink",
    "AVAXUSDT": "avalanche-2",
    "ATOMUSDT": "cosmos",
    "LTCUSDT": "litecoin",
    "UNIUSDT": "uniswap",
    "ETCUSDT": "ethereum-classic",
    "XLMUSDT": "stellar",
    "ALGOUSDT": "algorand",
    "TRXUSDT": "tron",
    "VETUSDT": "vechain",
    "FILUSDT": "filecoin",
}


class MarketDataFetcher:
    """Fetches market data from CoinGecko API"""
    
    def __init__(self):
        """Initialize CoinGecko fetcher"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.headers = {
            "User-Agent": "YAGATI-Brain/2.0 (Market Analysis Bot)",
            "Accept": "application/json",
        }
    
    def _get_coin_id(self, symbol: str) -> str:
        """Get CoinGecko coin ID from trading symbol"""
        if symbol not in SYMBOL_TO_COINGECKO_ID:
            raise ValueError(f"Symbol {symbol} not in CoinGecko mapping")
        return SYMBOL_TO_COINGECKO_ID[symbol]
    
    def _calculate_days(self, timeframe: str, limit: int) -> int:
        """Calculate days parameter for CoinGecko based on timeframe and limit"""
        # Map timeframe to hours
        tf_hours = {
            "1h": 1,
            "4h": 4,
            "1d": 24,
        }
        hours = tf_hours.get(timeframe, 1)
        days = (limit * hours) // 24 + 1
        return max(1, days)  # Minimum 1 day
    
    def _get_interval(self, timeframe: str) -> str:
        """Get CoinGecko interval from timeframe"""
        if timeframe == "1d":
            return "daily"
        return "hourly"
    
    def _convert_to_ohlc(self, cg_data: dict, timeframe: str, limit: int) -> List[Dict]:
        """Convert CoinGecko market_chart data to OHLC format"""
        # Extract prices and timestamps
        prices = cg_data.get("prices", [])
        volumes = cg_data.get("total_volumes", [])
        
        if not prices:
            return []
        
        # Group by interval
        tf_ms = {
            "1h": 3600000,
            "4h": 14400000,
            "1d": 86400000,
        }
        interval_ms = tf_ms.get(timeframe, 3600000)
        
        # Build OHLC candles
        candles = []
        current_interval_start = None
        interval_prices = []
        interval_volumes = []
        
        for i, (ts, price) in enumerate(prices):
            interval_start = (ts // interval_ms) * interval_ms
            
            if current_interval_start is None:
                current_interval_start = interval_start
            
            if interval_start != current_interval_start:
                # Close current candle
                if interval_prices:
                    candles.append({
                        "timestamp": current_interval_start // 1000,  # Convert to seconds
                        "open": interval_prices[0],
                        "high": max(interval_prices),
                        "low": min(interval_prices),
                        "close": interval_prices[-1],
                        "volume": sum(interval_volumes) if interval_volumes else 0,
                    })
                
                # Start new candle
                current_interval_start = interval_start
                interval_prices = [price]
                interval_volumes = [volumes[i][1]] if i < len(volumes) else []
            else:
                interval_prices.append(price)
                if i < len(volumes):
                    interval_volumes.append(volumes[i][1])
        
        # Close last candle
        if interval_prices:
            candles.append({
                "timestamp": current_interval_start // 1000,
                "open": interval_prices[0],
                "high": max(interval_prices),
                "low": min(interval_prices),
                "close": interval_prices[-1],
                "volume": sum(interval_volumes) if interval_volumes else 0,
            })
        
        # Return most recent `limit` candles
        return candles[-limit:]
    
    def fetch_ohlc(
        self, 
        symbol: str, 
        timeframe: str, 
        limit: int = OHLC_LIMIT
    ) -> Optional[List[Dict]]:
        """
        Fetch OHLC candle data from CoinGecko.
        
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
        
        max_retries = 3
        base_delay = 1  # seconds
        
        # Rate limiting: 2s between requests (30 calls/min)
        time.sleep(2.0)
        
        try:
            # Get CoinGecko ID
            coin_id = self._get_coin_id(symbol)
            
            # Calculate parameters
            days = self._calculate_days(timeframe, limit)
            interval = self._get_interval(timeframe)
            
            # Build URL
            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days,
                "interval": interval,
            }
            
            # Retry loop
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, headers=self.headers, params=params, timeout=30)
                    response.raise_for_status()
                    
                    # Convert to OHLC
                    cg_data = response.json()
                    ohlc = self._convert_to_ohlc(cg_data, timeframe, limit)
                    
                    if not ohlc:
                        raise Exception(f"No OHLC data returned for {symbol} {timeframe}")
                    
                    logger.info(f"Fetched {len(ohlc)} candles for {symbol} {timeframe} from CoinGecko")
                    return ohlc
                    
                except requests.exceptions.HTTPError as e:
                    status_code = e.response.status_code
                    source = "CoinGecko"
                    
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
                    source = "CoinGecko"
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
                    source = "CoinGecko"
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
            
            raise Exception(f"Failed to fetch {symbol} {timeframe} from CoinGecko after {max_retries} attempts")
            
        except ValueError as e:
            # Symbol not in mapping
            logger.error(f"Symbol mapping error: {e}", context={"symbol": symbol})
            raise Exception(f"Symbol mapping error: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error: {symbol} {timeframe}: {e}",
                context={"source": "CoinGecko", "error_type": type(e).__name__}
            )
            raise Exception(f"Unexpected error from CoinGecko fetching {symbol} {timeframe}: {e}")
    
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
