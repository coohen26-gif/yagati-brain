"""
Brain YAGATI v2 - Universe Filters Tests

Tests for stablecoin filtering and intersection logic.
"""

import sys
import os
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from brain_v2.universe.filters import (
    is_stablecoin,
    filter_stablecoins,
    normalize_symbol,
    compute_intersection,
)


class TestStablecoinFilter(unittest.TestCase):
    """Test stablecoin exclusion logic"""
    
    def test_identifies_major_stablecoins_by_symbol(self):
        """Test that major stablecoins are identified by symbol"""
        self.assertTrue(is_stablecoin("USDT"))
        self.assertTrue(is_stablecoin("usdt"))  # Case insensitive
        self.assertTrue(is_stablecoin("USDC"))
        self.assertTrue(is_stablecoin("DAI"))
        self.assertTrue(is_stablecoin("TUSD"))
        self.assertTrue(is_stablecoin("BUSD"))
    
    def test_identifies_stablecoins_by_id(self):
        """Test that stablecoins are identified by CoinGecko ID"""
        self.assertTrue(is_stablecoin("USDT", coin_id="tether"))
        self.assertTrue(is_stablecoin("USDC", coin_id="usd-coin"))
        self.assertTrue(is_stablecoin("DAI", coin_id="dai"))
    
    def test_does_not_identify_regular_crypto_as_stablecoin(self):
        """Test that regular cryptocurrencies are not flagged as stablecoins"""
        self.assertFalse(is_stablecoin("BTC", coin_id="bitcoin"))
        self.assertFalse(is_stablecoin("ETH", coin_id="ethereum"))
        self.assertFalse(is_stablecoin("SOL", coin_id="solana"))
        self.assertFalse(is_stablecoin("BNB", coin_id="binancecoin"))
    
    def test_filter_stablecoins_removes_stable_assets(self):
        """Test that filter_stablecoins removes stablecoin entries"""
        coins = [
            {"symbol": "BTC", "id": "bitcoin", "market_cap_rank": 1},
            {"symbol": "USDT", "id": "tether", "market_cap_rank": 3},
            {"symbol": "ETH", "id": "ethereum", "market_cap_rank": 2},
            {"symbol": "USDC", "id": "usd-coin", "market_cap_rank": 5},
            {"symbol": "SOL", "id": "solana", "market_cap_rank": 4},
        ]
        
        filtered = filter_stablecoins(coins)
        
        # Should only have BTC, ETH, SOL
        self.assertEqual(len(filtered), 3)
        
        symbols = [c["symbol"] for c in filtered]
        self.assertIn("BTC", symbols)
        self.assertIn("ETH", symbols)
        self.assertIn("SOL", symbols)
        self.assertNotIn("USDT", symbols)
        self.assertNotIn("USDC", symbols)


class TestSymbolNormalization(unittest.TestCase):
    """Test symbol normalization"""
    
    def test_normalize_to_uppercase(self):
        """Test that symbols are normalized to uppercase"""
        self.assertEqual(normalize_symbol("btc"), "BTC")
        self.assertEqual(normalize_symbol("eth"), "ETH")
        self.assertEqual(normalize_symbol("BTC"), "BTC")


class TestIntersection(unittest.TestCase):
    """Test intersection logic"""
    
    def test_basic_intersection(self):
        """Test basic intersection between CoinGecko and Bitget"""
        coingecko_coins = [
            {"symbol": "BTC", "id": "bitcoin", "market_cap_rank": 1},
            {"symbol": "ETH", "id": "ethereum", "market_cap_rank": 2},
            {"symbol": "SOL", "id": "solana", "market_cap_rank": 4},
            {"symbol": "ADA", "id": "cardano", "market_cap_rank": 5},
            {"symbol": "XRP", "id": "ripple", "market_cap_rank": 6},
        ]
        
        # Bitget has BTC, ETH, DOGE
        bitget_symbols = ["BTCUSDT", "ETHUSDT", "DOGEUSDT"]
        
        symbols, metadata = compute_intersection(coingecko_coins, bitget_symbols, target_size=50)
        
        # Should only have BTC and ETH (intersection)
        self.assertEqual(len(symbols), 2)
        self.assertIn("BTCUSDT", symbols)
        self.assertIn("ETHUSDT", symbols)
        self.assertNotIn("SOLUSDT", symbols)  # Not in Bitget
        self.assertNotIn("DOGEUSDT", symbols)  # Not in CoinGecko top
        
        # Check metadata
        self.assertEqual(metadata["coingecko_input_count"], 5)
        self.assertEqual(metadata["bitget_perp_markets"], 3)
        self.assertEqual(metadata["intersection_count"], 2)
    
    def test_intersection_respects_market_cap_order(self):
        """Test that intersection preserves CoinGecko market cap order"""
        coingecko_coins = [
            {"symbol": "BTC", "id": "bitcoin", "market_cap_rank": 1},
            {"symbol": "ETH", "id": "ethereum", "market_cap_rank": 2},
            {"symbol": "BNB", "id": "binancecoin", "market_cap_rank": 3},
            {"symbol": "SOL", "id": "solana", "market_cap_rank": 4},
        ]
        
        bitget_symbols = ["SOLUSDT", "BNBUSDT", "BTCUSDT", "ETHUSDT"]
        
        symbols, _ = compute_intersection(coingecko_coins, bitget_symbols, target_size=50)
        
        # Should be in market cap order: BTC, ETH, BNB, SOL
        self.assertEqual(symbols[0], "BTCUSDT")
        self.assertEqual(symbols[1], "ETHUSDT")
        self.assertEqual(symbols[2], "BNBUSDT")
        self.assertEqual(symbols[3], "SOLUSDT")
    
    def test_intersection_respects_target_size(self):
        """Test that intersection limits output to target_size"""
        coingecko_coins = [
            {"symbol": f"COIN{i}", "id": f"coin{i}", "market_cap_rank": i}
            for i in range(1, 101)
        ]
        
        # All coins available on Bitget
        bitget_symbols = [f"COIN{i}USDT" for i in range(1, 101)]
        
        symbols, metadata = compute_intersection(coingecko_coins, bitget_symbols, target_size=50)
        
        # Should only have 50 symbols
        self.assertEqual(len(symbols), 50)
        self.assertEqual(metadata["final_count"], 50)
    
    def test_intersection_handles_less_than_target(self):
        """Test behavior when intersection is less than target size"""
        coingecko_coins = [
            {"symbol": "BTC", "id": "bitcoin", "market_cap_rank": 1},
            {"symbol": "ETH", "id": "ethereum", "market_cap_rank": 2},
        ]
        
        bitget_symbols = ["BTCUSDT", "ETHUSDT"]
        
        symbols, metadata = compute_intersection(coingecko_coins, bitget_symbols, target_size=50)
        
        # Should have only 2 symbols (all available)
        self.assertEqual(len(symbols), 2)
        self.assertEqual(metadata["intersection_count"], 2)


if __name__ == "__main__":
    unittest.main()
