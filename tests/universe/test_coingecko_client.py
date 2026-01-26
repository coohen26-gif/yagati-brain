"""
Brain YAGATI v2 - CoinGecko Client Tests

Tests for CoinGecko API client with mocked responses.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from brain_v2.universe.coingecko_client import CoinGeckoClient


class TestCoinGeckoClient(unittest.TestCase):
    """Test CoinGecko API client"""
    
    def test_initialization(self):
        """Test client initialization with defaults"""
        client = CoinGeckoClient()
        
        self.assertEqual(client.vs_currency, "usd")
        self.assertEqual(client.base_url, "https://api.coingecko.com/api/v3")
        self.assertEqual(client.timeout, 30)
    
    def test_initialization_with_custom_params(self):
        """Test client initialization with custom parameters"""
        client = CoinGeckoClient(
            base_url="https://custom-api.example.com",
            vs_currency="eur",
            timeout=60
        )
        
        self.assertEqual(client.vs_currency, "eur")
        self.assertEqual(client.base_url, "https://custom-api.example.com")
        self.assertEqual(client.timeout, 60)
    
    @patch("brain_v2.universe.coingecko_client.requests.get")
    def test_fetch_top_coins_success(self, mock_get):
        """Test successful fetch of top coins"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"symbol": "btc", "id": "bitcoin", "market_cap_rank": 1},
            {"symbol": "eth", "id": "ethereum", "market_cap_rank": 2},
            {"symbol": "usdt", "id": "tether", "market_cap_rank": 3},
        ]
        mock_get.return_value = mock_response
        
        client = CoinGeckoClient()
        coins = client.fetch_top_coins(top_n=3)
        
        self.assertEqual(len(coins), 3)
        self.assertEqual(coins[0]["symbol"], "btc")
        self.assertEqual(coins[1]["symbol"], "eth")
        self.assertEqual(coins[2]["symbol"], "usdt")
        
        # Verify API was called with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("vs_currency", call_args[1]["params"])
        self.assertEqual(call_args[1]["params"]["vs_currency"], "usd")
        self.assertEqual(call_args[1]["params"]["order"], "market_cap_desc")
    
    @patch("brain_v2.universe.coingecko_client.requests.get")
    def test_fetch_top_coins_handles_pagination(self, mock_get):
        """Test that client handles pagination correctly"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"symbol": f"coin{i}", "id": f"coin{i}", "market_cap_rank": i}
            for i in range(1, 101)
        ]
        mock_get.return_value = mock_response
        
        client = CoinGeckoClient()
        coins = client.fetch_top_coins(top_n=100)
        
        # Should return 100 coins
        self.assertEqual(len(coins), 100)
    
    @patch("brain_v2.universe.coingecko_client.requests.get")
    @patch("brain_v2.universe.coingecko_client.time.sleep")  # Mock sleep to speed up test
    def test_fetch_top_coins_retries_on_failure(self, mock_sleep, mock_get):
        """Test retry logic on API failure"""
        # First two calls fail, third succeeds
        mock_get.side_effect = [
            Exception("Connection error"),
            Exception("Connection error"),
            MagicMock(
                status_code=200,
                json=lambda: [{"symbol": "btc", "id": "bitcoin", "market_cap_rank": 1}]
            )
        ]
        
        client = CoinGeckoClient()
        coins = client.fetch_top_coins(top_n=1, retry_count=3, retry_delay=1)
        
        # Should eventually succeed
        self.assertEqual(len(coins), 1)
        self.assertEqual(mock_get.call_count, 3)
    
    @patch("brain_v2.universe.coingecko_client.requests.get")
    @patch("brain_v2.universe.coingecko_client.time.sleep")
    def test_fetch_top_coins_fails_after_max_retries(self, mock_sleep, mock_get):
        """Test that client raises exception after max retries"""
        # All calls fail
        mock_get.side_effect = Exception("Connection error")
        
        client = CoinGeckoClient()
        
        with self.assertRaises(Exception) as context:
            client.fetch_top_coins(top_n=1, retry_count=3, retry_delay=1)
        
        self.assertIn("Failed to fetch CoinGecko data", str(context.exception))
        self.assertEqual(mock_get.call_count, 3)
    
    @patch("brain_v2.universe.coingecko_client.requests.get")
    def test_ping_success(self, mock_get):
        """Test ping returns True when API is reachable"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = CoinGeckoClient()
        result = client.ping()
        
        self.assertTrue(result)
    
    @patch("brain_v2.universe.coingecko_client.requests.get")
    def test_ping_failure(self, mock_get):
        """Test ping returns False when API is unreachable"""
        mock_get.side_effect = Exception("Network error")
        
        client = CoinGeckoClient()
        result = client.ping()
        
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
