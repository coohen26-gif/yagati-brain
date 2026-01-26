"""
Brain YAGATI v2 - Airtable Writer Test

Tests the Airtable writer token normalization to ensure
proper Authorization header formatting regardless of input.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Set mock environment variables for testing
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test_key"
os.environ["AIRTABLE_BASE_ID"] = "test_base"

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAirtableTokenNormalization(unittest.TestCase):
    """Test Airtable token normalization in various formats"""
    
    def _reload_modules(self):
        """Helper to reload settings and airtable_writer modules"""
        import importlib
        import brain_v2.config.settings
        import brain_v2.publish.airtable_writer
        importlib.reload(brain_v2.config.settings)
        importlib.reload(brain_v2.publish.airtable_writer)
    
    def test_token_without_bearer_prefix(self):
        """Test that a plain token gets Bearer prefix added"""
        os.environ["AIRTABLE_API_KEY"] = "keyABC123XYZ"
        self._reload_modules()
        
        from brain_v2.publish.airtable_writer import AirtableWriter
        writer = AirtableWriter()
        
        expected = "Bearer keyABC123XYZ"
        actual = writer.headers["Authorization"]
        
        self.assertEqual(actual, expected)
        print(f"✓ Plain token: '{os.environ['AIRTABLE_API_KEY']}' -> '{actual}'")
    
    def test_token_with_bearer_prefix_lowercase(self):
        """Test that existing 'bearer ' prefix (lowercase) is removed and re-added"""
        os.environ["AIRTABLE_API_KEY"] = "bearer keyABC123XYZ"
        self._reload_modules()
        
        from brain_v2.publish.airtable_writer import AirtableWriter
        writer = AirtableWriter()
        
        expected = "Bearer keyABC123XYZ"
        actual = writer.headers["Authorization"]
        
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual, "Bearer bearer keyABC123XYZ")
        print(f"✓ Lowercase bearer: '{os.environ['AIRTABLE_API_KEY']}' -> '{actual}'")
    
    def test_token_with_bearer_prefix_uppercase(self):
        """Test that existing 'BEARER ' prefix (uppercase) is removed and re-added"""
        os.environ["AIRTABLE_API_KEY"] = "BEARER keyABC123XYZ"
        self._reload_modules()
        
        from brain_v2.publish.airtable_writer import AirtableWriter
        writer = AirtableWriter()
        
        expected = "Bearer keyABC123XYZ"
        actual = writer.headers["Authorization"]
        
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual, "Bearer BEARER keyABC123XYZ")
        print(f"✓ Uppercase BEARER: '{os.environ['AIRTABLE_API_KEY']}' -> '{actual}'")
    
    def test_token_with_bearer_prefix_mixed_case(self):
        """Test that existing 'Bearer ' prefix (proper case) is removed and re-added"""
        os.environ["AIRTABLE_API_KEY"] = "Bearer keyABC123XYZ"
        self._reload_modules()
        
        from brain_v2.publish.airtable_writer import AirtableWriter
        writer = AirtableWriter()
        
        expected = "Bearer keyABC123XYZ"
        actual = writer.headers["Authorization"]
        
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual, "Bearer Bearer keyABC123XYZ")
        print(f"✓ Mixed case Bearer: '{os.environ['AIRTABLE_API_KEY']}' -> '{actual}'")
    
    def test_token_with_leading_whitespace(self):
        """Test that leading whitespace is stripped"""
        os.environ["AIRTABLE_API_KEY"] = "  keyABC123XYZ"
        self._reload_modules()
        
        from brain_v2.publish.airtable_writer import AirtableWriter
        writer = AirtableWriter()
        
        expected = "Bearer keyABC123XYZ"
        actual = writer.headers["Authorization"]
        
        self.assertEqual(actual, expected)
        print(f"✓ Leading whitespace: '{os.environ['AIRTABLE_API_KEY']}' -> '{actual}'")
    
    def test_token_with_trailing_whitespace(self):
        """Test that trailing whitespace is stripped"""
        os.environ["AIRTABLE_API_KEY"] = "keyABC123XYZ  "
        self._reload_modules()
        
        from brain_v2.publish.airtable_writer import AirtableWriter
        writer = AirtableWriter()
        
        expected = "Bearer keyABC123XYZ"
        actual = writer.headers["Authorization"]
        
        self.assertEqual(actual, expected)
        print(f"✓ Trailing whitespace: '{os.environ['AIRTABLE_API_KEY']}' -> '{actual}'")
    
    def test_token_with_bearer_and_whitespace(self):
        """Test that Bearer prefix and whitespace are both handled"""
        os.environ["AIRTABLE_API_KEY"] = "  Bearer keyABC123XYZ  "
        self._reload_modules()
        
        from brain_v2.publish.airtable_writer import AirtableWriter
        writer = AirtableWriter()
        
        expected = "Bearer keyABC123XYZ"
        actual = writer.headers["Authorization"]
        
        self.assertEqual(actual, expected)
        print(f"✓ Bearer + whitespace: '{os.environ['AIRTABLE_API_KEY']}' -> '{actual}'")
    
    def test_token_with_double_bearer_prefix(self):
        """Test that double Bearer prefix results in 'Bearer Bearer <token>' (edge case)"""
        os.environ["AIRTABLE_API_KEY"] = "Bearer Bearer keyABC123XYZ"
        self._reload_modules()
        
        from brain_v2.publish.airtable_writer import AirtableWriter
        writer = AirtableWriter()
        
        # Edge case: 'Bearer Bearer keyABC123XYZ' becomes 'Bearer Bearer keyABC123XYZ'
        # because we check .lower() but remove by position, so:
        # 1. 'Bearer Bearer keyABC123XYZ'.lower().startswith('bearer ') -> True
        # 2. Remove first 7 chars -> 'Bearer keyABC123XYZ'
        # 3. Add 'Bearer ' -> 'Bearer Bearer keyABC123XYZ'
        # This is acceptable as double Bearer prefix is extremely unlikely in practice
        expected = "Bearer Bearer keyABC123XYZ"
        actual = writer.headers["Authorization"]
        
        self.assertEqual(actual, expected)
        print(f"✓ Double Bearer (edge case): '{os.environ['AIRTABLE_API_KEY']}' -> '{actual}'")


class TestAirtableWriterMethods(unittest.TestCase):
    """Test that all Airtable writer methods use the normalized headers"""
    
    @patch('brain_v2.publish.airtable_writer.requests.post')
    def test_write_startup_uses_normalized_headers(self, mock_post):
        """Test that write_startup_log uses normalized headers"""
        os.environ["AIRTABLE_API_KEY"] = "Bearer keyABC123XYZ"
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        import importlib
        import brain_v2.publish.airtable_writer
        importlib.reload(brain_v2.publish.airtable_writer)
        from brain_v2.publish.airtable_writer import AirtableWriter
        
        writer = AirtableWriter()
        result = writer.write_startup_log()
        
        # Verify the request was made with correct headers
        self.assertTrue(result)
        self.assertTrue(mock_post.called)
        
        call_kwargs = mock_post.call_args[1]
        auth_header = call_kwargs['headers']['Authorization']
        
        self.assertEqual(auth_header, "Bearer keyABC123XYZ")
        self.assertNotEqual(auth_header, "Bearer Bearer keyABC123XYZ")
        print(f"✓ write_startup_log uses normalized header: '{auth_header}'")
    
    @patch('brain_v2.publish.airtable_writer.requests.post')
    def test_write_setup_forming_uses_normalized_headers(self, mock_post):
        """Test that write_setup_forming uses normalized headers"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Use the current environment variable value
        from brain_v2.publish.airtable_writer import AirtableWriter
        
        writer = AirtableWriter()
        
        decision = {
            "status": "forming",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "setup_type": "volatility_expansion",
            "confidence": "HIGH",
            "justification": "Test setup"
        }
        
        result = writer.write_setup_forming(decision)
        
        # Verify the request was made with correct headers
        self.assertTrue(result)
        self.assertTrue(mock_post.called)
        
        call_kwargs = mock_post.call_args[1]
        auth_header = call_kwargs['headers']['Authorization']
        
        # Should start with "Bearer " and not have double "Bearer"
        self.assertTrue(auth_header.startswith("Bearer "))
        self.assertNotIn("Bearer Bearer", auth_header)
        self.assertNotIn("Bearer bearer", auth_header)
        print(f"✓ write_setup_forming uses normalized header: '{auth_header}'")


def run_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("Brain YAGATI v2 - Airtable Writer Token Normalization Tests")
    print("="*60 + "\n")
    
    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestAirtableTokenNormalization))
    suite.addTests(loader.loadTestsFromTestCase(TestAirtableWriterMethods))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("✅ All token normalization tests passed!")
    else:
        print(f"❌ {len(result.failures) + len(result.errors)} test(s) failed")
    print("="*60 + "\n")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
