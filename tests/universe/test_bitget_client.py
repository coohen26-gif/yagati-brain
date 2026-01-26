"""
Brain YAGATI v2 - Bitget Client Tests

Tests for Bitget API client with mocked responses.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from brain_v2.universe.bitget_client import BitgetClient


class TestBitgetClient(unittest.TestCase):
    """Test Bitget API client"""
    
    def test_initialization(self):
        """Test client initialization with defaults"""
        client = BitgetClient()
        
        self.assertEqual(client.base_url, "https://api.bitget.com")
        self.assertEqual(client.timeout, 30)
    
    def test_initialization_with_custom_params(self):
        """Test client initialization with custom parameters"""
        client = BitgetClient(
            base_url="https://custom-api.example.com",
            timeout=60
        )
        
        self.assertEqual(client.base_url, "https://custom-api.example.com")
        self.assertEqual(client.timeout, 60)
    
    def test_normalize_bitget_symbol(self):
        """Test symbol normalization from Bitget format"""
        # Test with UMCBL suffix
        self.assertEqual(
            BitgetClient.normalize_bitget_symbol("BTCUSDT_UMCBL"),
            "BTCUSDT"
        )
        self.assertEqual(
            BitgetClient.normalize_bitget_symbol("ETHUSDT_UMCBL"),
            "ETHUSDT"
        )
        
        # Test without suffix (already normalized)
        self.assertEqual(
            BitgetClient.normalize_bitget_symbol("BTCUSDT"),
            "BTCUSDT"
        )
    
    @patch("brain_v2.universe.bitget_client.requests.get")
    def test_fetch_usdt_perpetual_markets_success(self, mock_get):
        """Test successful fetch of USDT perpetual markets"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "00000",
            "msg": "success",
            "data": [
                {
                    "symbol": "BTCUSDT_UMCBL",
                    "supportMarginCoins": ["USDT"],
                    "baseCoin": "BTC",
                    "quoteCoin": "USDT"
                },
                {
                    "symbol": "ETHUSDT_UMCBL",
                    "supportMarginCoins": ["USDT"],
                    "baseCoin": "ETH",
                    "quoteCoin": "USDT"
                },
                {
                    "symbol": "SOLUSDT_UMCBL",
                    "supportMarginCoins": ["USDT"],
                    "baseCoin": "SOL",
                    "quoteCoin": "USDT"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = BitgetClient()
        symbols = client.fetch_usdt_perpetual_markets()
        
        # Should return normalized symbols
        self.assertEqual(len(symbols), 3)
        self.assertIn("BTCUSDT", symbols)
        self.assertIn("ETHUSDT", symbols)
        self.assertIn("SOLUSDT", symbols)
        
        # Verify API was called with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("productType", call_args[1]["params"])
        self.assertEqual(call_args[1]["params"]["productType"], "umcbl")
    
    @patch("brain_v2.universe.bitget_client.requests.get")
    def test_fetch_usdt_perpetual_markets_filters_inactive(self, mock_get):
        """Test that inactive markets are filtered out"""
        # Mock response with both active and inactive contracts
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "00000",
            "msg": "success",
            "data": [
                {
                    "symbol": "BTCUSDT_UMCBL",
                    "supportMarginCoins": ["USDT"],  # Active
                },
                {
                    "symbol": "OLDCOINUSDT_UMCBL",
                    "supportMarginCoins": None,  # Inactive
                },
                {
                    "symbol": "ETHUSDT_UMCBL",
                    "supportMarginCoins": ["USDT"],  # Active
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = BitgetClient()
        symbols = client.fetch_usdt_perpetual_markets()
        
        # Should only include active markets
        self.assertEqual(len(symbols), 2)
        self.assertIn("BTCUSDT", symbols)
        self.assertIn("ETHUSDT", symbols)
        self.assertNotIn("OLDCOINUSDT", symbols)
    
    @patch("brain_v2.universe.bitget_client.requests.get")
    @patch("brain_v2.universe.bitget_client.time.sleep")
    def test_fetch_usdt_perpetual_markets_retries_on_failure(self, mock_sleep, mock_get):
        """Test retry logic on API failure"""
        # First two calls fail, third succeeds
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "code": "00000",
            "data": [
                {"symbol": "BTCUSDT_UMCBL", "supportMarginCoins": ["USDT"]}
            ]
        }
        
        mock_get.side_effect = [
            Exception("Connection error"),
            Exception("Connection error"),
            success_response
        ]
        
        client = BitgetClient()
        symbols = client.fetch_usdt_perpetual_markets(retry_count=3, retry_delay=1)
        
        # Should eventually succeed
        self.assertEqual(len(symbols), 1)
        self.assertIn("BTCUSDT", symbols)
        self.assertEqual(mock_get.call_count, 3)
    
    @patch("brain_v2.universe.bitget_client.requests.get")
    @patch("brain_v2.universe.bitget_client.time.sleep")
    def test_fetch_usdt_perpetual_markets_fails_after_max_retries(self, mock_sleep, mock_get):
        """Test that client raises exception after max retries"""
        # All calls fail
        mock_get.side_effect = Exception("Connection error")
        
        client = BitgetClient()
        
        with self.assertRaises(Exception) as context:
            client.fetch_usdt_perpetual_markets(retry_count=3, retry_delay=1)
        
        self.assertIn("Failed to fetch Bitget data", str(context.exception))
        self.assertEqual(mock_get.call_count, 3)
    
    @patch("brain_v2.universe.bitget_client.requests.get")
    def test_ping_success(self, mock_get):
        """Test ping returns True when API is reachable"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = BitgetClient()
        result = client.ping()
        
        self.assertTrue(result)
    
    @patch("brain_v2.universe.bitget_client.requests.get")
    def test_ping_failure(self, mock_get):
        """Test ping returns False when API is unreachable"""
        mock_get.side_effect = Exception("Network error")
        
        client = BitgetClient()
        result = client.ping()
        
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
