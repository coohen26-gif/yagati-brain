"""
Brain YAGATI v2 - Build Universe Integration Tests

End-to-end tests for the universe builder with mocked API responses.
"""

import sys
import os
import unittest
import json
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from brain_v2.universe.build_universe import (
    get_env_config,
    build_universe,
    write_universe_json,
)


class TestBuildUniverse(unittest.TestCase):
    """Test end-to-end universe building"""
    
    @patch("brain_v2.universe.build_universe.BitgetClient")
    @patch("brain_v2.universe.build_universe.CoinGeckoClient")
    def test_build_universe_success(self, mock_coingecko_cls, mock_bitget_cls):
        """Test successful universe building"""
        # Mock CoinGecko client
        mock_cg_client = MagicMock()
        mock_cg_client.fetch_top_coins.return_value = [
            {"symbol": "btc", "id": "bitcoin", "market_cap_rank": 1},
            {"symbol": "eth", "id": "ethereum", "market_cap_rank": 2},
            {"symbol": "usdt", "id": "tether", "market_cap_rank": 3},  # Stablecoin
            {"symbol": "bnb", "id": "binancecoin", "market_cap_rank": 4},
            {"symbol": "sol", "id": "solana", "market_cap_rank": 5},
            {"symbol": "usdc", "id": "usd-coin", "market_cap_rank": 6},  # Stablecoin
        ]
        mock_coingecko_cls.return_value = mock_cg_client
        
        # Mock Bitget client
        mock_bg_client = MagicMock()
        mock_bg_client.fetch_usdt_perpetual_markets.return_value = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"
        ]
        mock_bitget_cls.return_value = mock_bg_client
        
        # Build universe
        config = {
            "coingecko_vs_currency": "usd",
            "coingecko_top_n": 6,
            "bitget_api_base_url": "https://api.bitget.com",
            "target_size": 50,
            "output_path": "/tmp/test_universe.json"
        }
        
        universe_data = build_universe(config)
        
        # Validate structure
        self.assertIn("generated_at", universe_data)
        self.assertIn("market", universe_data)
        self.assertIn("source", universe_data)
        self.assertIn("symbols", universe_data)
        self.assertIn("metadata", universe_data)
        
        # Validate market
        self.assertEqual(universe_data["market"], "bitget_usdt_perp")
        
        # Validate source
        self.assertEqual(universe_data["source"]["coingecko_top_n"], 6)
        self.assertEqual(universe_data["source"]["target_size"], 50)
        
        # Validate symbols (should exclude stablecoins USDT, USDC)
        symbols = universe_data["symbols"]
        self.assertIn("BTCUSDT", symbols)
        self.assertIn("ETHUSDT", symbols)
        self.assertIn("BNBUSDT", symbols)
        self.assertIn("SOLUSDT", symbols)
        
        # Stablecoins should be excluded
        # ADA should not be in result (not in CoinGecko top after stablecoin filtering)
        
        # Validate metadata
        metadata = universe_data["metadata"]
        self.assertEqual(metadata["coingecko_fetched"], 6)
        self.assertEqual(metadata["after_stable_exclusion"], 4)  # Excluded USDT, USDC
        self.assertEqual(metadata["bitget_perp_markets"], 5)
        self.assertGreater(metadata["intersection_count"], 0)
    
    @patch("brain_v2.universe.build_universe.BitgetClient")
    @patch("brain_v2.universe.build_universe.CoinGeckoClient")
    def test_build_universe_respects_target_size(self, mock_coingecko_cls, mock_bitget_cls):
        """Test that universe respects target size limit"""
        # Mock CoinGecko with 100 coins
        mock_cg_client = MagicMock()
        mock_cg_client.fetch_top_coins.return_value = [
            {"symbol": f"coin{i}", "id": f"coin{i}", "market_cap_rank": i}
            for i in range(1, 101)
        ]
        mock_coingecko_cls.return_value = mock_cg_client
        
        # Mock Bitget with all 100 coins available
        mock_bg_client = MagicMock()
        mock_bg_client.fetch_usdt_perpetual_markets.return_value = [
            f"COIN{i}USDT" for i in range(1, 101)
        ]
        mock_bitget_cls.return_value = mock_bg_client
        
        # Build universe with target_size = 50
        config = {
            "coingecko_vs_currency": "usd",
            "coingecko_top_n": 100,
            "bitget_api_base_url": "https://api.bitget.com",
            "target_size": 50,
            "output_path": "/tmp/test_universe.json"
        }
        
        universe_data = build_universe(config)
        
        # Should have exactly 50 symbols
        self.assertEqual(len(universe_data["symbols"]), 50)
        self.assertEqual(universe_data["metadata"]["final_count"], 50)
    
    def test_json_output_validation(self):
        """Test JSON output structure and format"""
        universe_data = {
            "generated_at": datetime.now().isoformat(),
            "market": "bitget_usdt_perp",
            "source": {
                "coingecko_top_n": 100,
                "target_size": 50
            },
            "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "metadata": {
                "coingecko_fetched": 100,
                "after_stable_exclusion": 85,
                "bitget_perp_markets": 200,
                "intersection_count": 3,
                "final_count": 3
            }
        }
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            write_universe_json(universe_data, temp_path)
            
            # Verify file exists
            self.assertTrue(os.path.exists(temp_path))
            
            # Load and validate JSON
            with open(temp_path, 'r') as f:
                loaded_data = json.load(f)
            
            # Validate structure
            self.assertEqual(loaded_data["market"], "bitget_usdt_perp")
            self.assertIsInstance(loaded_data["symbols"], list)
            self.assertEqual(len(loaded_data["symbols"]), 3)
            self.assertIn("BTCUSDT", loaded_data["symbols"])
            
            # Validate ISO 8601 timestamp format
            self.assertIn("T", loaded_data["generated_at"])
            
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_get_env_config_defaults(self):
        """Test that get_env_config returns correct defaults"""
        # Clear any existing env vars
        for key in ["UNIVERSE_OUTPUT_PATH", "COINGECKO_VS_CURRENCY", 
                    "COINGECKO_TOP_N", "BITGET_API_BASE_URL"]:
            if key in os.environ:
                del os.environ[key]
        
        config = get_env_config()
        
        self.assertEqual(config["output_path"], "/opt/yagati/data/universe_usdt_perp.json")
        self.assertEqual(config["coingecko_vs_currency"], "usd")
        self.assertEqual(config["coingecko_top_n"], 100)
        self.assertEqual(config["bitget_api_base_url"], "https://api.bitget.com")
        self.assertEqual(config["target_size"], 50)
    
    def test_get_env_config_respects_env_vars(self):
        """Test that get_env_config respects environment variables"""
        # Set custom env vars
        os.environ["UNIVERSE_OUTPUT_PATH"] = "/custom/path/universe.json"
        os.environ["COINGECKO_VS_CURRENCY"] = "eur"
        os.environ["COINGECKO_TOP_N"] = "200"
        os.environ["BITGET_API_BASE_URL"] = "https://custom.api.com"
        
        try:
            config = get_env_config()
            
            self.assertEqual(config["output_path"], "/custom/path/universe.json")
            self.assertEqual(config["coingecko_vs_currency"], "eur")
            self.assertEqual(config["coingecko_top_n"], 200)
            self.assertEqual(config["bitget_api_base_url"], "https://custom.api.com")
            
        finally:
            # Cleanup env vars
            for key in ["UNIVERSE_OUTPUT_PATH", "COINGECKO_VS_CURRENCY", 
                        "COINGECKO_TOP_N", "BITGET_API_BASE_URL"]:
                if key in os.environ:
                    del os.environ[key]


if __name__ == "__main__":
    unittest.main()
