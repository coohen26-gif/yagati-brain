#!/usr/bin/env python3
"""
Publish and synchronize strategies from JSON files to Supabase 'strategies' table.

This script:
1. Loads strategy JSON files from:
   - brain_day/strategies_day/ (DAY horizon)
   - brain/ core_strategy_*.json files (SWING horizon)
2. Extracts metadata (strategy_key, horizon, arena, family, risk_level)
3. Upserts records into Supabase 'strategies' table
"""

import os
import json
import glob
import requests
from pathlib import Path

# =============================
# CONFIG
# =============================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing")

HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
}

# Paths relative to repository root
REPO_ROOT = Path(__file__).parent.parent
DAY_STRATEGIES_DIR = REPO_ROOT / "brain_day" / "strategies_day"
SWING_STRATEGIES_DIR = REPO_ROOT / "brain"

# =============================
# HELPERS
# =============================

def load_json_file(filepath):
    """Load and parse a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_day_strategies():
    """
    Load all DAY strategy JSON files from brain_day/strategies_day/.
    
    Returns:
        list: List of strategy records with extracted metadata
    """
    strategies = []
    pattern = str(DAY_STRATEGIES_DIR / "day_strategy_*.json")
    
    for filepath in glob.glob(pattern):
        try:
            data = load_json_file(filepath)
            
            # Extract required fields
            record = {
                "strategy_key": data.get("strategy_key"),
                "horizon": "DAY",  # Set as DAY for all files in this directory
                "arena": "DAY",    # Determine dynamically: DAY -> DAY
                "family": data.get("strategy_family"),
                "risk_level": data.get("risk_level"),
                "source": "brain_day/strategies_day"
            }
            
            # Validate required fields
            if not record["strategy_key"]:
                print(f"⚠️  Skipping {filepath}: missing strategy_key")
                continue
            
            strategies.append(record)
            
        except Exception as e:
            print(f"❌ Error loading {filepath}: {e}")
    
    return strategies


def load_swing_strategies():
    """
    Load all SWING strategy JSON files from brain/core_strategy_*.json.
    
    Note: The problem statement mentions brain/swing_alpha/ but this directory
    doesn't exist. Using core_strategy_*.json files instead.
    
    Returns:
        list: List of strategy records with extracted metadata
    """
    strategies = []
    pattern = str(SWING_STRATEGIES_DIR / "core_strategy_*.json")
    
    for filepath in glob.glob(pattern):
        try:
            data = load_json_file(filepath)
            
            # Extract strategy_key (try both strategy_id and strategy_key fields)
            strategy_key = data.get("strategy_key") or data.get("strategy_id")
            
            # Try to extract family from various possible fields
            family = None
            
            # First try top-level concept field
            if "concept" in data:
                family = data.get("concept")
            # Then try strategy_family
            elif "strategy_family" in data:
                family = data.get("strategy_family")
            # Finally try rules.market_regime
            else:
                rules = data.get("rules", {})
                if "market_regime" in rules:
                    family = rules["market_regime"]
            
            # SWING strategies don't have explicit risk_level in JSON
            # Set to None for now
            risk_level = data.get("risk_level")
            
            record = {
                "strategy_key": strategy_key,
                "horizon": "SWING",
                "arena": "SWING_ALPHA",
                "family": family,
                "risk_level": risk_level,
                "source": "brain/core_strategy"
            }
            
            # Validate required fields
            if not record["strategy_key"]:
                print(f"⚠️  Skipping {filepath}: missing strategy_key/strategy_id")
                continue
            
            strategies.append(record)
            
        except Exception as e:
            print(f"❌ Error loading {filepath}: {e}")
    
    return strategies


def upsert_strategies(strategies):
    """
    Upsert strategy records to Supabase 'strategies' table.
    
    Args:
        strategies (list): List of strategy records to upsert
    """
    if not strategies:
        print("⚠️  No strategies to upsert")
        return
    
    url = f"{SUPABASE_URL}/rest/v1/strategies"
    
    # Use merge-duplicates to upsert based on primary key
    r = requests.post(
        url,
        headers={**HEADERS, "Prefer": "resolution=merge-duplicates"},
        json=strategies,
        timeout=20,
    )
    
    r.raise_for_status()
    print(f"✅ Successfully upserted {len(strategies)} strategies")


# =============================
# MAIN
# =============================

def main():
    """Main execution function."""
    print("📡 Loading and publishing strategies to Supabase...")
    
    # Load strategies from both sources
    day_strategies = load_day_strategies()
    print(f"📊 Loaded {len(day_strategies)} DAY strategies")
    
    swing_strategies = load_swing_strategies()
    print(f"📊 Loaded {len(swing_strategies)} SWING strategies")
    
    # Combine all strategies
    all_strategies = day_strategies + swing_strategies
    
    if not all_strategies:
        print("⚠️  No strategies found to publish")
        return
    
    # Display summary
    print(f"\n📋 Summary:")
    print(f"  - Total strategies: {len(all_strategies)}")
    print(f"  - DAY: {len(day_strategies)}")
    print(f"  - SWING: {len(swing_strategies)}")
    
    # Upsert to Supabase
    print(f"\n🚀 Publishing to Supabase...")
    upsert_strategies(all_strategies)
    
    print("\n✅ Strategy synchronization complete!")


if __name__ == "__main__":
    main()
