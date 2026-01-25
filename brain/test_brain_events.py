#!/usr/bin/env python3
"""
Test script for YAGATI-BRAIN-002 scan and observation events.
This script verifies that the brain can log scan and observation events to Airtable.

Usage:
    1. Set environment variables:
       export AIRTABLE_API_KEY=your_api_key
       export AIRTABLE_BASE_ID=your_base_id
    
    2. Run the test:
       python3 brain/test_brain_events.py
"""

import sys
import os

# Add brain directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from airtable_logger import log_brain_scan, log_brain_observation

def main():
    print("=" * 50)
    print("YAGATI-BRAIN-002 Scan & Observation Events Test")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    
    if not api_key:
        print("❌ AIRTABLE_API_KEY environment variable not set")
        print("\nPlease set it with:")
        print("  export AIRTABLE_API_KEY=your_api_key")
        return 1
    
    if not base_id:
        print("❌ AIRTABLE_BASE_ID environment variable not set")
        print("\nPlease set it with:")
        print("  export AIRTABLE_BASE_ID=your_base_id")
        return 1
    
    print(f"✅ AIRTABLE_API_KEY: {api_key[:10]}...")
    print(f"✅ AIRTABLE_BASE_ID: {base_id}")
    print()
    
    # Test 1: Log a scan event for BTC
    print("Test 1: Logging scan event for BTC...")
    success1 = log_brain_scan("BTC", note="scanning market regime")
    
    if success1:
        print("✅ SUCCESS: Scan event logged for BTC")
    else:
        print("❌ FAILED: Could not log scan event for BTC")
    
    # Test 2: Log a scan event for GLOBAL
    print("\nTest 2: Logging scan event for GLOBAL...")
    success2 = log_brain_scan("GLOBAL", note="fetching signals from API")
    
    if success2:
        print("✅ SUCCESS: Scan event logged for GLOBAL")
    else:
        print("❌ FAILED: Could not log scan event for GLOBAL")
    
    # Test 3: Log a scan event for a specific symbol
    print("\nTest 3: Logging scan event for BTCUSDT...")
    success3 = log_brain_scan("BTCUSDT", note="analyzing signal")
    
    if success3:
        print("✅ SUCCESS: Scan event logged for BTCUSDT")
    else:
        print("❌ FAILED: Could not log scan event for BTCUSDT")
    
    # Test 4: Log an observation event with neutral status
    print("\nTest 4: Logging observation event (neutral)...")
    success4 = log_brain_observation("BTC", status="neutral", note="regime: TREND (UP)")
    
    if success4:
        print("✅ SUCCESS: Observation event logged (neutral)")
    else:
        print("❌ FAILED: Could not log observation event (neutral)")
    
    # Test 5: Log an observation event with weak status
    print("\nTest 5: Logging observation event (weak)...")
    success5 = log_brain_observation("ETHUSDT", status="weak", note="RSI divergence")
    
    if success5:
        print("✅ SUCCESS: Observation event logged (weak)")
    else:
        print("❌ FAILED: Could not log observation event (weak)")
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    total_tests = 5
    passed_tests = sum([success1, success2, success3, success4, success5])
    
    print(f"Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("\n✅ ALL TESTS PASSED")
        print("\nCheck your Airtable base:")
        print(f"  https://airtable.com/{base_id}")
        print("\nYou should see new records in 'brain_logs' table with:")
        print("  - cycle_type: scan (3 records)")
        print("  - cycle_type: observation (2 records)")
        print("  - Various context values (BTC, GLOBAL, BTCUSDT, ETHUSDT)")
        print("  - status: ok (for scan), neutral/weak (for observation)")
        return 0
    else:
        print(f"\n❌ {total_tests - passed_tests} TESTS FAILED")
        print("\nPossible issues:")
        print("  1. Invalid API key or base ID")
        print("  2. Table 'brain_logs' doesn't exist in your base")
        print("  3. Missing required fields in the table")
        print("  4. Network connectivity issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
