#!/usr/bin/env python3
"""
Test script for V1.1.3-01 Market Scanner

Tests the market scanning and setup detection functionality.

Usage:
    1. Set environment variables:
       export AIRTABLE_API_KEY=your_api_key
       export AIRTABLE_BASE_ID=your_base_id
       export SUPABASE_URL=your_supabase_url
       export SUPABASE_ANON_KEY=your_supabase_key
    
    2. Run the test:
       python3 brain/test_market_scanner.py
"""

import sys
import os
from pathlib import Path

# Load .env file explicitly
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
    print("✅ .env file loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")
except Exception as e:
    print(f"⚠️ Error loading .env file: {e}")

# Add brain directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from market_scanner import (
    scan_all_markets,
    scan_symbol_timeframe,
    MARKET_UNIVERSE,
    TIMEFRAMES
)
from setup_logger import log_setups_to_airtable


def test_environment_variables():
    """Test that required environment variables are set."""
    print("\n" + "=" * 50)
    print("Test 1: Environment Variables")
    print("=" * 50)
    
    required_vars = [
        "AIRTABLE_API_KEY",
        "AIRTABLE_BASE_ID",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY"
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show truncated value for security
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing.append(var)
    
    if missing:
        print(f"\n❌ Missing variables: {', '.join(missing)}")
        return False
    else:
        print("\n✅ All environment variables set")
        return True


def test_single_scan():
    """Test scanning a single symbol on a single timeframe."""
    print("\n" + "=" * 50)
    print("Test 2: Single Symbol Scan")
    print("=" * 50)
    
    symbol = "BTCUSDT"
    timeframe = "1d"
    
    print(f"\nScanning {symbol} on {timeframe} timeframe...")
    
    try:
        setups = scan_symbol_timeframe(symbol, timeframe)
        
        if setups:
            print(f"✅ SUCCESS: Found {len(setups)} setup(s)")
            for setup in setups:
                print(f"\n  Setup: {setup['setup_type']}")
                print(f"  Confidence: {setup['confidence']}")
                print(f"  Context: {setup['context']}")
        else:
            print("ℹ️ No setups detected (this is normal if market is quiet)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_market_scan():
    """Test scanning all markets across all timeframes."""
    print("\n" + "=" * 50)
    print("Test 3: Full Market Scan")
    print("=" * 50)
    
    print(f"\nScanning {len(MARKET_UNIVERSE)} symbols across {len(TIMEFRAMES)} timeframes...")
    print(f"Symbols: {', '.join(MARKET_UNIVERSE)}")
    print(f"Timeframes: {', '.join(TIMEFRAMES)}")
    
    try:
        setups = scan_all_markets()
        
        print(f"\n✅ SUCCESS: Scan completed")
        print(f"Total setups detected: {len(setups)}")
        
        if setups:
            # Group by setup type
            by_type = {}
            for setup in setups:
                setup_type = setup['setup_type']
                if setup_type not in by_type:
                    by_type[setup_type] = []
                by_type[setup_type].append(setup)
            
            print("\nSetups by type:")
            for setup_type, items in by_type.items():
                print(f"  {setup_type}: {len(items)}")
        else:
            print("ℹ️ No setups detected (this is normal if market is quiet)")
        
        return setups
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_airtable_logging(setups):
    """Test logging setups to Airtable."""
    print("\n" + "=" * 50)
    print("Test 4: Airtable Logging")
    print("=" * 50)
    
    if not setups:
        print("ℹ️ No setups to log - skipping Airtable test")
        print("(You can manually create test data or wait for market conditions)")
        return True
    
    print(f"\nLogging {len(setups)} setup(s) to Airtable...")
    
    try:
        success_count = log_setups_to_airtable(setups)
        
        if success_count > 0:
            print(f"\n✅ SUCCESS: Logged {success_count}/{len(setups)} setups")
            print("\nCheck your Airtable base:")
            print(f"  https://airtable.com/{os.getenv('AIRTABLE_BASE_ID')}")
            print("\nLook for new records in 'setups_forming' table with:")
            print("  - symbol (e.g., BTCUSDT)")
            print("  - timeframe (e.g., 1h, 4h, 1d)")
            print("  - setup_type (e.g., volatility_expansion)")
            print("  - confidence (LOW, MEDIUM, HIGH)")
            print("  - status (FORMING)")
            return True
        else:
            print(f"\n⚠️ WARNING: No setups were logged")
            print("This could mean:")
            print("  1. Airtable not configured")
            print("  2. Table 'setups_forming' doesn't exist")
            print("  3. Network or API issues")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("V1.1.3-01 Market Scanner Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test 1: Environment variables
    results.append(test_environment_variables())
    
    if not results[0]:
        print("\n❌ Cannot proceed without environment variables")
        return 1
    
    # Test 2: Single scan
    results.append(test_single_scan())
    
    # Test 3: Full market scan
    setups = test_full_market_scan()
    results.append(setups is not None)
    
    # Test 4: Airtable logging (only if we have setups)
    if setups is not None:
        results.append(test_airtable_logging(setups))
    else:
        results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        print("\n✨ Market scanner is ready to use")
        print("\nNext steps:")
        print("  1. Ensure 'setups_forming' table exists in Airtable with fields:")
        print("     - symbol (text)")
        print("     - timeframe (text)")
        print("     - setup_type (text)")
        print("     - status (text)")
        print("     - confidence (text)")
        print("     - detected_at (datetime)")
        print("     - context (long text)")
        print("  2. Run the brain loop to start continuous scanning")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        print("\nTroubleshooting:")
        print("  1. Check environment variables")
        print("  2. Verify Supabase connection")
        print("  3. Ensure Airtable table exists")
        print("  4. Check network connectivity")
        return 1


if __name__ == "__main__":
    sys.exit(main())
