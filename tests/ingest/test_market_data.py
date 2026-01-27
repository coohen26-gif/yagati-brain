"""
Brain YAGATI v2 - Market Data Fetcher Tests

Tests for NATIVE OHLC fetching from CoinGecko /ohlc endpoint.
"""

import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from brain_v2.ingest.market_data import (
    MarketDataFetcher, 
    load_symbol_mapping,
    MAX_API_CALLS_PER_CYCLE
)


class TestSymbolMapping(unittest.TestCase):
    """Test symbol mapping loading"""
    
    @patch("builtins.open", new_callable=mock_open, read_data='{"mappings": {"BTCUSDT": "bitcoin", "ETHUSDT": "ethereum"}}')
    @patch("os.path.exists", return_value=True)
    def test_load_symbol_mapping_success(self, mock_exists, mock_file):
        """Test successful symbol mapping load"""
        mappings = load_symbol_mapping()
        self.assertIsInstance(mappings, dict)
        self.assertEqual(mappings["BTCUSDT"], "bitcoin")
        self.assertEqual(mappings["ETHUSDT"], "ethereum")
    
    @patch("os.path.exists", return_value=False)
    def test_load_symbol_mapping_file_not_found(self, mock_exists):
        """Test error when mapping file doesn't exist"""
        with self.assertRaises(FileNotFoundError):
            load_symbol_mapping()
    
    @patch("builtins.open", new_callable=mock_open, read_data='invalid json')
    @patch("os.path.exists", return_value=True)
    def test_load_symbol_mapping_invalid_json(self, mock_exists, mock_file):
        """Test error when mapping file has invalid JSON"""
        with self.assertRaises(ValueError):
            load_symbol_mapping()


class TestMarketDataFetcher(unittest.TestCase):
    """Test MarketDataFetcher class"""
    
    @patch("brain_v2.ingest.market_data.load_symbol_mapping")
    @patch("brain_v2.ingest.market_data.get_logger")
    def setUp(self, mock_logger, mock_load_mapping):
        """Set up test fixtures"""
        # Mock symbol mapping
        mock_load_mapping.return_value = {
            "BTCUSDT": "bitcoin",
            "ETHUSDT": "ethereum",
            "SOLUSDT": "solana"
        }
        mock_logger.return_value = MagicMock()
        self.fetcher = MarketDataFetcher()
    
    def test_initialization(self):
        """Test fetcher initialization"""
        self.assertEqual(self.fetcher.base_url, "https://api.coingecko.com/api/v3")
        self.assertIn("User-Agent", self.fetcher.headers)
        self.assertIn("Accept", self.fetcher.headers)
        self.assertEqual(self.fetcher.api_call_count, 0)
        self.assertIsNotNone(self.fetcher.symbol_mapping)
    
    def test_reset_api_call_count(self):
        """Test API call counter reset"""
        self.fetcher.api_call_count = 50
        self.fetcher.reset_api_call_count()
        self.assertEqual(self.fetcher.api_call_count, 0)
    
    @patch("brain_v2.ingest.market_data.get_logger")
    def test_check_rate_limit_within_limit(self, mock_logger):
        """Test rate limit check when within limit"""
        mock_logger.return_value = MagicMock()
        self.fetcher.api_call_count = 50
        result = self.fetcher.check_rate_limit(estimated_calls=10)
        self.assertTrue(result)
    
    @patch("brain_v2.ingest.market_data.get_logger")
    def test_check_rate_limit_exceeds_limit(self, mock_logger):
        """Test rate limit check when exceeding limit"""
        mock_logger.return_value = MagicMock()
        self.fetcher.api_call_count = 95
        result = self.fetcher.check_rate_limit(estimated_calls=10)
        self.assertFalse(result)
    
    def test_get_coin_id_valid_symbol(self):
        """Test getting CoinGecko ID for valid symbol"""
        coin_id = self.fetcher._get_coin_id("BTCUSDT")
        self.assertEqual(coin_id, "bitcoin")
        
        coin_id = self.fetcher._get_coin_id("ETHUSDT")
        self.assertEqual(coin_id, "ethereum")
    
    def test_get_coin_id_invalid_symbol(self):
        """Test getting CoinGecko ID for invalid symbol raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.fetcher._get_coin_id("INVALIDUSDT")
        
        self.assertIn("not in CoinGecko mapping", str(context.exception))
    
    def test_map_timeframe_to_days(self):
        """Test timeframe to days mapping"""
        # 1h -> 1 day (gets 4h candles)
        days = self.fetcher._map_timeframe_to_days("1h")
        self.assertEqual(days, 1)
        
        # 4h -> 7 days
        days = self.fetcher._map_timeframe_to_days("4h")
        self.assertEqual(days, 7)
        
        # 1d -> 180 days
        days = self.fetcher._map_timeframe_to_days("1d")
        self.assertEqual(days, 180)
    
    @patch("brain_v2.ingest.market_data.time.sleep")
    @patch("brain_v2.ingest.market_data.requests.get")
    @patch("brain_v2.ingest.market_data.get_logger")
    def test_fetch_ohlc_success(self, mock_logger, mock_get, mock_sleep):
        """Test successful OHLC fetch from CoinGecko /ohlc endpoint"""
        # Mock logger
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        # Mock successful API response - CoinGecko /ohlc format
        # Returns: [[timestamp_ms, open, high, low, close], ...]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [1000000000000, 50000.0, 51000.0, 49000.0, 50500.0],
            [1000003600000, 50500.0, 52000.0, 50000.0, 51500.0],
        ]
        mock_get.return_value = mock_response
        
        # Call fetch_ohlc
        ohlc = self.fetcher.fetch_ohlc("BTCUSDT", "1h", 10)
        
        # Verify results
        self.assertIsNotNone(ohlc)
        self.assertIsInstance(ohlc, list)
        self.assertEqual(len(ohlc), 2)
        
        # Check structure
        self.assertIn("timestamp", ohlc[0])
        self.assertIn("open", ohlc[0])
        self.assertIn("high", ohlc[0])
        self.assertIn("low", ohlc[0])
        self.assertIn("close", ohlc[0])
        self.assertIn("volume", ohlc[0])
        
        # Check values
        self.assertEqual(ohlc[0]["open"], 50000.0)
        self.assertEqual(ohlc[0]["high"], 51000.0)
        self.assertEqual(ohlc[0]["low"], 49000.0)
        self.assertEqual(ohlc[0]["close"], 50500.0)
        
        # Verify API was called with correct URL and params
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("/coins/bitcoin/ohlc", call_args[0][0])
        self.assertEqual(call_args[1]["params"]["vs_currency"], "usd")
        self.assertIn("days", call_args[1]["params"])
        
        # Verify rate limiting was applied
        mock_sleep.assert_called()
        
        # Verify API call was counted
        self.assertEqual(self.fetcher.api_call_count, 1)
    
    @patch("brain_v2.ingest.market_data.time.sleep")
    @patch("brain_v2.ingest.market_data.get_logger")
    def test_fetch_ohlc_rate_limit_exceeded(self, mock_logger, mock_sleep):
        """Test fetch_ohlc when rate limit is exceeded"""
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        # Set API call count to exceed limit
        self.fetcher.api_call_count = MAX_API_CALLS_PER_CYCLE
        
        with self.assertRaises(Exception) as context:
            self.fetcher.fetch_ohlc("BTCUSDT", "1h", 10)
        
        self.assertIn("API call limit exceeded", str(context.exception))
    
    @patch("brain_v2.ingest.market_data.time.sleep")
    @patch("brain_v2.ingest.market_data.requests.get")
    @patch("brain_v2.ingest.market_data.get_logger")
    def test_fetch_ohlc_invalid_symbol(self, mock_logger, mock_get, mock_sleep):
        """Test fetch_ohlc with invalid symbol"""
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        with self.assertRaises(Exception) as context:
            self.fetcher.fetch_ohlc("INVALIDUSDT", "1h", 10)
        
        self.assertIn("Symbol mapping error", str(context.exception))
    
    @patch("brain_v2.ingest.market_data.time.sleep")
    @patch("brain_v2.ingest.market_data.get_logger")
    def test_fetch_multiple_timeframes(self, mock_logger, mock_sleep):
        """Test fetching multiple timeframes"""
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        # Mock fetch_ohlc to return simple data
        with patch.object(self.fetcher, 'fetch_ohlc') as mock_fetch:
            mock_fetch.return_value = [
                {"timestamp": 1000000000, "open": 50000, "high": 51000, "low": 49000, "close": 50500, "volume": 0}
            ]
            
            results = self.fetcher.fetch_multiple_timeframes("BTCUSDT", ["1h", "4h", "1d"])
            
            # Should have results for all timeframes
            self.assertEqual(len(results), 3)
            self.assertIn("1h", results)
            self.assertIn("4h", results)
            self.assertIn("1d", results)
            
            # Each timeframe should have data
            self.assertIsNotNone(results["1h"])
            self.assertIsNotNone(results["4h"])
            self.assertIsNotNone(results["1d"])


if __name__ == "__main__":
    unittest.main()
