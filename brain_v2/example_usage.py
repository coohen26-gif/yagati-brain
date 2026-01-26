#!/usr/bin/env python3
"""
Brain YAGATI v2 - Quick Start Example

This example demonstrates how to use Brain v2 programmatically
in your own scripts or applications.
"""

import os
import sys

# Set up environment (use real credentials in production)
os.environ["SUPABASE_URL"] = "https://your-project.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "your_anon_key_here"
os.environ["AIRTABLE_API_KEY"] = "your_airtable_key_here"
os.environ["AIRTABLE_BASE_ID"] = "your_base_id_here"

# Add brain_v2 to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brain_v2.ingest.market_data import MarketDataFetcher
from brain_v2.features.technical import compute_features
from brain_v2.detect.setup_detector import detect_setups
from brain_v2.decide.decision_engine import make_decisions
from brain_v2.governance.logger import get_logger


def analyze_single_symbol(symbol, timeframe):
    """
    Analyze a single symbol/timeframe combination.
    
    Returns:
        List of decisions
    """
    logger = get_logger()
    
    # Fetch market data
    logger.info(f"Analyzing {symbol} {timeframe}")
    fetcher = MarketDataFetcher()
    
    try:
        candles = fetcher.fetch_ohlc(symbol, timeframe)
        
        if not candles:
            logger.error(f"No data for {symbol} {timeframe}")
            return []
        
        # Compute features
        features = compute_features(candles)
        
        # Detect setups
        setups = detect_setups(features, symbol, timeframe)
        
        if not setups:
            logger.info(f"No setups detected for {symbol} {timeframe}")
            return []
        
        # Make decisions
        decisions = make_decisions(setups, features)
        
        # Log results
        for decision in decisions:
            logger.log_decision(decision)
            
            if decision['status'] == 'forming':
                print(f"\n🎯 FORMING SETUP DETECTED:")
                print(f"   Symbol: {decision['symbol']} {decision['timeframe']}")
                print(f"   Type: {decision['setup_type']}")
                print(f"   Score: {decision['score']}/100")
                print(f"   Confidence: {decision['confidence']}")
                print(f"   Reason: {decision['justification']}")
            else:
                print(f"\n❌ Setup rejected: {decision['symbol']} {decision['timeframe']}")
                print(f"   Reason: {decision['justification']}")
        
        return decisions
        
    except Exception as e:
        logger.log_error_explicit(e, f"{symbol}_{timeframe}")
        print(f"❌ Error analyzing {symbol} {timeframe}: {e}")
        return []


def main():
    """Main example"""
    print("\n" + "="*60)
    print("Brain YAGATI v2 - Quick Start Example")
    print("="*60 + "\n")
    
    # Example: Analyze Bitcoin on 4-hour timeframe
    decisions = analyze_single_symbol("BTCUSDT", "4h")
    
    print(f"\n📊 Analysis complete: {len(decisions)} decision(s) made")
    
    # Count forming setups
    forming = sum(1 for d in decisions if d['status'] == 'forming')
    rejected = sum(1 for d in decisions if d['status'] == 'reject')
    
    print(f"   - Forming: {forming}")
    print(f"   - Rejected: {rejected}")
    
    # Note: In production, you would write these to Airtable
    # using brain_v2.publish.airtable_writer


if __name__ == "__main__":
    main()
