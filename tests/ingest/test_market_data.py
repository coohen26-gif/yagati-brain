"""
Brain YAGATI v2 - Market Data Fetcher Tests

Tests for market data fetching from CoinGecko API with mocked responses.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock, Mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from brain_v2.ingest.market_data import MarketDataFetcher, SYMBOL_TO_COINGECKO_ID


class TestMarketDataFetcher(unittest.TestCase):
    """Test MarketDataFetcher class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.fetcher = MarketDataFetcher()
    
    def test_initialization(self):
        """Test fetcher initialization"""
        self.assertEqual(self.fetcher.base_url, "https://api.coingecko.com/api/v3")
        self.assertIn("User-Agent", self.fetcher.headers)
        self.assertIn("Accept", self.fetcher.headers)
    
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
    
    def test_calculate_days(self):
        """Test days calculation for different timeframes"""
        # 1h: 260 candles * 1 hour = 260 hours / 24 = 10.83 days -> 11 days
        days = self.fetcher._calculate_days("1h", 260)
        self.assertEqual(days, 11)
        
        # 4h: 260 candles * 4 hours = 1040 hours / 24 = 43.33 days -> 44 days
        days = self.fetcher._calculate_days("4h", 260)
        self.assertEqual(days, 44)
        
        # 1d: 260 candles * 24 hours = 6240 hours / 24 = 260 days
        days = self.fetcher._calculate_days("1d", 260)
        self.assertEqual(days, 261)
    
    def test_get_interval(self):
        """Test interval mapping"""
        self.assertEqual(self.fetcher._get_interval("1h"), "hourly")
        self.assertEqual(self.fetcher._get_interval("4h"), "hourly")
        self.assertEqual(self.fetcher._get_interval("1d"), "daily")
    
    def test_convert_to_ohlc_empty_data(self):
        """Test OHLC conversion with empty data"""
        cg_data = {"prices": [], "total_volumes": []}
        ohlc = self.fetcher._convert_to_ohlc(cg_data, "1h", 10)
        self.assertEqual(ohlc, [])
    
    def test_convert_to_ohlc_hourly(self):
        """Test OHLC conversion for hourly data"""
        # Create mock data aligned to hour boundaries
        # All timestamps aligned to hourly intervals (multiples of 3600000 ms)
        base_ts = 1000000000000  # Base timestamp
        hour_ms = 3600000  # 1 hour in milliseconds
        
        cg_data = {
            "prices": [
                [base_ts, 50000.0],                    # Hour 0
                [base_ts + hour_ms, 51000.0],          # Hour 1
                [base_ts + 2 * hour_ms, 50500.0],      # Hour 2
                [base_ts + 3 * hour_ms, 49500.0],      # Hour 3
            ],
            "total_volumes": [
                [base_ts, 1000.0],
                [base_ts + hour_ms, 1100.0],
                [base_ts + 2 * hour_ms, 900.0],
                [base_ts + 3 * hour_ms, 1200.0],
            ]
        }
        
        ohlc = self.fetcher._convert_to_ohlc(cg_data, "1h", 10)
        
        # Should have 4 candles (one per hour)
        self.assertEqual(len(ohlc), 4)
        
        # Check first candle structure
        self.assertIn("timestamp", ohlc[0])
        self.assertIn("open", ohlc[0])
        self.assertIn("high", ohlc[0])
        self.assertIn("low", ohlc[0])
        self.assertIn("close", ohlc[0])
        self.assertIn("volume", ohlc[0])
        
        # Verify first candle values (only one price point, so OHLC all equal)
        self.assertEqual(ohlc[0]["open"], 50000.0)
        self.assertEqual(ohlc[0]["close"], 50000.0)
    
    @patch("brain_v2.ingest.market_data.time.sleep")
    @patch("brain_v2.ingest.market_data.requests.get")
    @patch("brain_v2.ingest.market_data.get_logger")
    def test_fetch_ohlc_success(self, mock_logger, mock_get, mock_sleep):
        """Test successful OHLC fetch from CoinGecko"""
        # Mock logger
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "prices": [
                [1000000000000, 50000.0],
                [1000003600000, 50500.0],
            ],
            "total_volumes": [
                [1000000000000, 1000.0],
                [1000003600000, 1100.0],
            ]
        }
        mock_get.return_value = mock_response
        
        # Call fetch_ohlc
        ohlc = self.fetcher.fetch_ohlc("BTCUSDT", "1h", 10)
        
        # Verify results
        self.assertIsNotNone(ohlc)
        self.assertIsInstance(ohlc, list)
        self.assertGreater(len(ohlc), 0)
        
        # Verify API was called with correct URL and params
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("/coins/bitcoin/market_chart", call_args[0][0])
        self.assertEqual(call_args[1]["params"]["vs_currency"], "usd")
        self.assertIn("days", call_args[1]["params"])
        self.assertEqual(call_args[1]["params"]["interval"], "hourly")
        
        # Verify rate limiting was applied
        mock_sleep.assert_called()
    
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
    @patch("brain_v2.ingest.market_data.requests.get")
    @patch("brain_v2.ingest.market_data.get_logger")
    def test_fetch_ohlc_retries_on_500_error(self, mock_logger, mock_get, mock_sleep):
        """Test that fetch_ohlc retries on 500 errors"""
        import requests
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        # Create mock responses
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "prices": [[1000000000000, 50000.0]],
            "total_volumes": [[1000000000000, 1000.0]]
        }
        
        # Create error responses that properly mimic HTTPError
        def make_500_error():
            error_resp = MagicMock()
            error_resp.status_code = 500
            http_error = requests.exceptions.HTTPError("500 Server Error")
            http_error.response = error_resp
            
            mock_req = MagicMock()
            mock_req.raise_for_status.side_effect = http_error
            return mock_req
        
        # First two calls return 500, third succeeds
        mock_get.side_effect = [
            make_500_error(),
            make_500_error(),
            success_response
        ]
        
        # Should eventually succeed
        ohlc = self.fetcher.fetch_ohlc("BTCUSDT", "1h", 10)
        self.assertIsNotNone(ohlc)
        self.assertEqual(mock_get.call_count, 3)
    
    @patch("brain_v2.ingest.market_data.time.sleep")
    @patch("brain_v2.ingest.market_data.get_logger")
    def test_fetch_multiple_timeframes(self, mock_logger, mock_sleep):
        """Test fetching multiple timeframes"""
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        # Mock fetch_ohlc to return simple data
        with patch.object(self.fetcher, 'fetch_ohlc') as mock_fetch:
            mock_fetch.return_value = [{"timestamp": 1000000000, "open": 50000}]
            
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
    
    def test_symbol_mapping_coverage(self):
        """Test that symbol mapping includes all expected symbols"""
        expected_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
        
        for symbol in expected_symbols:
            self.assertIn(symbol, SYMBOL_TO_COINGECKO_ID)
            self.assertIsInstance(SYMBOL_TO_COINGECKO_ID[symbol], str)
            self.assertGreater(len(SYMBOL_TO_COINGECKO_ID[symbol]), 0)


if __name__ == "__main__":
    unittest.main()
