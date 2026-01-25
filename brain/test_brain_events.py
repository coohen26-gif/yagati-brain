#!/usr/bin/env python3
"""
Test script for YAGATI-BRAIN-002 scan and observation events.
This script verifies that the new logging functions work correctly.

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
    
    # Test 1: Log scan event for BTC
    print("Test 1: Logging scan event for BTC...")
    success1 = log_brain_scan("BTC", note="scanning market regime")
    if success1:
        print("✅ Scan event logged successfully")
    else:
        print("❌ Failed to log scan event")
    print()
    
    # Test 2: Log scan event for GLOBAL
    print("Test 2: Logging scan event for GLOBAL...")
    success2 = log_brain_scan("GLOBAL", note="fetching signals from API")
    if success2:
        print("✅ Scan event logged successfully")
    else:
        print("❌ Failed to log scan event")
    print()
    
    # Test 3: Log scan event for a symbol
    print("Test 3: Logging scan event for BTCUSDT...")
    success3 = log_brain_scan("BTCUSDT", note="analyzing signal")
    if success3:
        print("✅ Scan event logged successfully")
    else:
        print("❌ Failed to log scan event")
    print()
    
    # Test 4: Log observation event with neutral status
    print("Test 4: Logging observation event (neutral)...")
    success4 = log_brain_observation("BTC", status="neutral", note="regime: TREND (UP)")
    if success4:
        print("✅ Observation event logged successfully")
    else:
        print("❌ Failed to log observation event")
    print()
    
    # Test 5: Log observation event with weak status
    print("Test 5: Logging observation event (weak)...")
    success5 = log_brain_observation("ETHUSDT", status="weak", note="RSI divergence")
    if success5:
        print("✅ Observation event logged successfully")
    else:
        print("❌ Failed to log observation event")
    print()
    
    # Summary
    all_success = all([success1, success2, success3, success4, success5])
    
    if all_success:
        print("\n✅ SUCCESS: All events logged to Airtable!")
        print("\nCheck your Airtable base:")
        print(f"  https://airtable.com/{base_id}")
        print("\nLook for new records in the 'brain_logs' table with:")
        print("  - cycle_type: scan (Tests 1-3)")
        print("  - cycle_type: observation (Tests 4-5)")
        print("  - Various context values: BTC, GLOBAL, BTCUSDT, ETHUSDT")
        print("  - status: ok (for scans), neutral/weak (for observations)")
        return 0
    else:
        print("\n❌ FAILED: Some events could not be logged to Airtable")
        print("\nPossible issues:")
        print("  1. Invalid API key or base ID")
        print("  2. Table 'brain_logs' doesn't exist in your base")
        print("  3. Missing required fields in the table")
        print("  4. Network connectivity issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
