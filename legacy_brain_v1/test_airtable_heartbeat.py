#!/usr/bin/env python3
"""
Test script for YAGATI-BRAIN-001 Airtable heartbeat integration.
This script verifies that the Airtable logger can log a heartbeat record.

Usage:
    1. Set environment variables:
       export AIRTABLE_API_KEY=your_api_key
       export AIRTABLE_BASE_ID=your_base_id
    
    2. Run the test:
       python3 brain/test_airtable_heartbeat.py
"""

import sys
import os

# Add brain directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from airtable_logger import log_brain_heartbeat

def main():
    print("=" * 50)
    print("YAGATI-BRAIN-001 Airtable Heartbeat Test")
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
    
    print("Attempting to log heartbeat to Airtable...")
    success = log_brain_heartbeat()
    
    if success:
        print("\n✅ SUCCESS: Heartbeat logged to Airtable!")
        print("\nCheck your Airtable base:")
        print(f"  https://airtable.com/{base_id}")
        print("\nLook for a new record in the 'brain_logs' table with:")
        print("  - timestamp: (current time)")
        print("  - cycle_type: heartbeat")
        print("  - context: GLOBAL")
        print("  - status: ok")
        print("  - note: initial brain heartbeat")
        return 0
    else:
        print("\n❌ FAILED: Could not log heartbeat to Airtable")
        print("\nPossible issues:")
        print("  1. Invalid API key or base ID")
        print("  2. Table 'brain_logs' doesn't exist in your base")
        print("  3. Missing required fields in the table")
        print("  4. Network connectivity issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
