#!/usr/bin/env python3
"""
Test script for YAGATI-BRAIN-002 cognitive events (scan & observation).
This script verifies that scan and observation events can be logged to Airtable.

Usage:
    1. Set environment variables:
       export AIRTABLE_API_KEY=your_api_key
       export AIRTABLE_BASE_ID=your_base_id
       export SUPABASE_URL=your_supabase_url
       export SUPABASE_ANON_KEY=your_supabase_key
    
    2. Run the test:
       python3 brain/test_cognitive_events.py
"""

import sys
import os

# Add brain directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from airtable_logger import log_brain_scan, log_brain_observation
from brain_cognitive_events import log_cognitive_events


def test_scan_event():
    """Test logging a single scan event."""
    print("\n" + "=" * 50)
    print("Test 1: Scan Event")
    print("=" * 50)
    
    success = log_brain_scan("BTCUSDT", note="test market scan")
    
    if success:
        print("✅ SUCCESS: Scan event logged to Airtable!")
        print("\nExpected record in brain_logs:")
        print("  - cycle_type: scan")
        print("  - context: BTCUSDT")
        print("  - status: ok")
        print("  - note: test market scan")
        return True
    else:
        print("❌ FAILED: Could not log scan event")
        return False


def test_observation_event():
    """Test logging a single observation event."""
    print("\n" + "=" * 50)
    print("Test 2: Observation Event")
    print("=" * 50)
    
    success = log_brain_observation(
        symbol="ETHUSDT",
        status="neutral",
        note="test regime transition"
    )
    
    if success:
        print("✅ SUCCESS: Observation event logged to Airtable!")
        print("\nExpected record in brain_logs:")
        print("  - cycle_type: observation")
        print("  - context: ETHUSDT")
        print("  - status: neutral")
        print("  - note: test regime transition")
        return True
    else:
        print("❌ FAILED: Could not log observation event")
        return False


def test_full_cognitive_cycle():
    """Test the full cognitive events cycle."""
    print("\n" + "=" * 50)
    print("Test 3: Full Cognitive Events Cycle")
    print("=" * 50)
    
    success = log_cognitive_events()
    
    if success:
        print("✅ SUCCESS: Full cognitive events cycle completed!")
        print("\nCheck your Airtable base for:")
        print("  - Multiple scan events (BTCUSDT, ETHUSDT, SOLUSDT)")
        print("  - Observation events (if patterns detected)")
        return True
    else:
        print("❌ FAILED: Cognitive events cycle failed")
        return False


def main():
    print("=" * 50)
    print("YAGATI-BRAIN-002 Cognitive Events Test")
    print("=" * 50)
    
    # Check environment variables
    airtable_key = os.getenv("AIRTABLE_API_KEY")
    airtable_base = os.getenv("AIRTABLE_BASE_ID")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    missing = []
    if not airtable_key:
        missing.append("AIRTABLE_API_KEY")
    if not airtable_base:
        missing.append("AIRTABLE_BASE_ID")
    if not supabase_url:
        missing.append("SUPABASE_URL")
    if not supabase_key:
        missing.append("SUPABASE_ANON_KEY")
    
    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        print("\nPlease set all required variables:")
        for var in missing:
            print(f"  export {var}=your_value")
        return 1
    
    print(f"✅ AIRTABLE_API_KEY: {airtable_key[:10]}...")
    print(f"✅ AIRTABLE_BASE_ID: {airtable_base}")
    print(f"✅ SUPABASE_URL: {supabase_url}")
    print()
    
    # Run tests
    results = []
    results.append(test_scan_event())
    results.append(test_observation_event())
    results.append(test_full_cognitive_cycle())
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        print("\nCheck your Airtable base:")
        print(f"  https://airtable.com/{airtable_base}")
        print("\nLook for new records in the 'brain_logs' table with:")
        print("  - cycle_type: scan (multiple records)")
        print("  - cycle_type: observation (if patterns detected)")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        print("\nPossible issues:")
        print("  1. Invalid API key or base ID")
        print("  2. Table 'brain_logs' doesn't exist in your base")
        print("  3. Missing required fields in the table")
        print("  4. Network connectivity issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
