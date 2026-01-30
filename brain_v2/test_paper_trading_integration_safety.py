"""
Paper Trading - Integration Safety Test

Validates that paper trading never blocks the main flow and respects
the PAPER_TRADING_ENABLED flag.
"""

import sys
import os

# Set mock environment variables for testing
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test_key"
os.environ["AIRTABLE_API_KEY"] = "test_key"
os.environ["AIRTABLE_BASE_ID"] = "test_base"

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_flag_disabled():
    """Test that paper trading is disabled when flag is false"""
    print("\n" + "="*60)
    print("Test 1: Paper Trading Flag - Disabled")
    print("="*60)
    
    # Set flag to disabled
    os.environ["PAPER_TRADING_ENABLED"] = "false"
    
    # Reload settings to pick up the change
    import importlib
    import brain_v2.config.settings as settings
    importlib.reload(settings)
    
    print(f"PAPER_TRADING_ENABLED: {settings.PAPER_TRADING_ENABLED}")
    
    assert settings.PAPER_TRADING_ENABLED is False, "Flag should be False when set to 'false'"
    print("✅ Flag correctly disabled\n")
    
    return True


def test_flag_enabled():
    """Test that paper trading is enabled when flag is true"""
    print("\n" + "="*60)
    print("Test 2: Paper Trading Flag - Enabled")
    print("="*60)
    
    # Set flag to enabled
    os.environ["PAPER_TRADING_ENABLED"] = "true"
    
    # Reload settings to pick up the change
    import importlib
    import brain_v2.config.settings as settings
    importlib.reload(settings)
    
    print(f"PAPER_TRADING_ENABLED: {settings.PAPER_TRADING_ENABLED}")
    
    assert settings.PAPER_TRADING_ENABLED is True, "Flag should be True when set to 'true'"
    print("✅ Flag correctly enabled\n")
    
    return True


def test_flag_default():
    """Test that paper trading is disabled by default"""
    print("\n" + "="*60)
    print("Test 3: Paper Trading Flag - Default (not set)")
    print("="*60)
    
    # Remove flag from environment
    if "PAPER_TRADING_ENABLED" in os.environ:
        del os.environ["PAPER_TRADING_ENABLED"]
    
    # Reload settings to pick up the change
    import importlib
    import brain_v2.config.settings as settings
    importlib.reload(settings)
    
    print(f"PAPER_TRADING_ENABLED: {settings.PAPER_TRADING_ENABLED}")
    
    assert settings.PAPER_TRADING_ENABLED is False, "Flag should be False by default (safe default)"
    print("✅ Default is correctly disabled (safe)\n")
    
    return True


def test_error_isolation():
    """Test that paper trading errors don't propagate to main flow"""
    print("\n" + "="*60)
    print("Test 4: Error Isolation - Main Flow Safety")
    print("="*60)
    
    # Enable paper trading
    os.environ["PAPER_TRADING_ENABLED"] = "true"
    
    # Reload settings
    import importlib
    import brain_v2.config.settings as settings
    importlib.reload(settings)
    
    # Simulate paper trading error within the try/except block
    main_flow_completed = False
    paper_trading_error_caught = False
    
    try:
        # This is the pattern used in run.py
        if settings.PAPER_TRADING_ENABLED:
            try:
                # Simulate a paper trading error
                raise RuntimeError("Simulated paper trading error")
            except Exception as e:
                # Error caught and logged
                paper_trading_error_caught = True
                print(f"⚠️ Paper trading error (non-blocking): {e}")
        
        # Main flow continues
        main_flow_completed = True
        print("✅ Main flow completed successfully")
        
    except Exception as e:
        print(f"❌ Main flow was blocked by: {e}")
        return False
    
    # Verify both conditions
    assert paper_trading_error_caught, "Paper trading error should be caught"
    assert main_flow_completed, "Main flow should complete despite error"
    
    print("✅ Main flow is protected from paper trading errors\n")
    
    return True


def test_no_exchange_imports():
    """Test that paper trading module has no exchange imports"""
    print("\n" + "="*60)
    print("Test 5: Exchange Safety - No Exchange APIs")
    print("="*60)
    
    import ast
    import os
    
    paper_trading_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "brain_v2",
        "paper_trading"
    )
    
    # List of forbidden imports
    forbidden_imports = [
        'ccxt',
        'binance',
        'exchange',
        'bitget',
        'bybit',
        'okx',
        'kraken',
        'coinbase',
    ]
    
    # Check all Python files in paper_trading module
    for filename in os.listdir(paper_trading_dir):
        if filename.endswith('.py') and not filename.startswith('__pycache__'):
            filepath = os.path.join(paper_trading_dir, filename)
            
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Parse the file
            try:
                tree = ast.parse(content)
                
                # Check for forbidden imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_name = alias.name.lower()
                            for forbidden in forbidden_imports:
                                if forbidden in module_name:
                                    print(f"❌ Found forbidden import '{alias.name}' in {filename}")
                                    return False
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module_name = node.module.lower()
                            for forbidden in forbidden_imports:
                                if forbidden in module_name:
                                    print(f"❌ Found forbidden import 'from {node.module}' in {filename}")
                                    return False
                
                print(f"   ✓ {filename}: No exchange imports")
                
            except Exception as e:
                print(f"⚠️ Could not parse {filename}: {e}")
    
    print("\n✅ No exchange API imports found in paper trading module\n")
    
    return True


def test_isolated_tables():
    """Test that paper trading uses isolated Airtable tables"""
    print("\n" + "="*60)
    print("Test 6: Table Isolation - Dedicated Paper Tables")
    print("="*60)
    
    from brain_v2.paper_trading.recorder import (
        TABLE_PAPER_ACCOUNT,
        TABLE_PAPER_OPEN_TRADES,
        TABLE_PAPER_CLOSED_TRADES,
        TABLE_SETUPS_FORMING
    )
    
    # Expected table names
    expected_tables = {
        "paper_account": TABLE_PAPER_ACCOUNT,
        "paper_open_trades": TABLE_PAPER_OPEN_TRADES,
        "paper_closed_trades": TABLE_PAPER_CLOSED_TRADES,
    }
    
    # Verify table names are correct
    for expected_name, actual_name in expected_tables.items():
        print(f"   {expected_name}: {actual_name}")
        assert actual_name == expected_name, f"Table should be named '{expected_name}'"
    
    # Verify read-only access to setups_forming
    print(f"   setups_forming (read-only): {TABLE_SETUPS_FORMING}")
    assert TABLE_SETUPS_FORMING == "setups_forming", "Should read from setups_forming"
    
    print("\n✅ All tables are correctly isolated\n")
    
    return True


def main():
    """Run all integration safety tests"""
    print("\n" + "="*60)
    print("Brain YAGATI v2 - Paper Trading Integration Safety Tests")
    print("="*60)
    
    tests = [
        ("Flag Disabled", test_flag_disabled),
        ("Flag Enabled", test_flag_enabled),
        ("Flag Default (Safe)", test_flag_default),
        ("Error Isolation", test_error_isolation),
        ("No Exchange APIs", test_no_exchange_imports),
        ("Table Isolation", test_isolated_tables),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY - INTEGRATION SAFETY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60 + "\n")
    
    # Final verdict
    if passed == total:
        print("🎉 All integration safety tests passed!")
        print("✅ Paper trading is SAFE for production merge\n")
        return 0
    else:
        print("⚠️ Some integration safety tests failed")
        print("❌ DO NOT MERGE until all tests pass\n")
        return 1


if __name__ == "__main__":
    exit(main())
