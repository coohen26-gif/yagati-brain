"""
Brain YAGATI v2 - Main Entry Point

Deterministic decision module for market analysis.

Flow:
1. Startup: Log heartbeat to Airtable
2. Fetch market data (real, no fake data)
3. Compute features (deterministic)
4. Detect setups (forming only)
5. Make decisions (scored, justified)
6. Write to Airtable (brain_logs + setups_forming)
7. Explicit error logging (no silent failures)

Usage:
    python brain_v2/run.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain_v2.config.settings import TIMEFRAMES
from brain_v2.config.symbols import SYMBOL_UNIVERSE
from brain_v2.ingest.market_data import MarketDataFetcher
from brain_v2.features.technical import compute_features
from brain_v2.detect.setup_detector import detect_setups
from brain_v2.decide.decision_engine import make_decisions
from brain_v2.publish.airtable_writer import write_startup, write_cycle, write_decisions, AirtableWriter
from brain_v2.governance.logger import get_logger


def analyze_symbol(symbol: str, timeframe: str, logger, fetcher):
    """
    Analyze a single symbol/timeframe combination.
    
    Args:
        symbol: Market symbol
        timeframe: Timeframe
        logger: Governance logger
        fetcher: Market data fetcher
        
    Returns:
        List of decisions
    """
    try:
        # Fetch market data
        logger.info(f"Fetching {symbol} {timeframe}")
        candles = fetcher.fetch_ohlc(symbol, timeframe)
        
        if not candles:
            logger.error(f"No market data for {symbol} {timeframe}")
            logger.log_market_data_fetch(symbol, timeframe, success=False)
            return []
        
        logger.log_market_data_fetch(symbol, timeframe, success=True)
        
        # Compute features
        logger.info(f"Computing features for {symbol} {timeframe}")
        features = compute_features(candles)
        
        if not features:
            logger.warning(f"No features computed for {symbol} {timeframe}")
            return []
        
        # Detect setups
        logger.info(f"Detecting setups for {symbol} {timeframe}")
        setups = detect_setups(features, symbol, timeframe)
        
        if not setups:
            logger.info(f"No setups detected for {symbol} {timeframe}")
            return []
        
        logger.info(f"Detected {len(setups)} setup(s) for {symbol} {timeframe}")
        
        # Make decisions
        decisions = make_decisions(setups, features)
        
        # Log each decision
        for decision in decisions:
            logger.log_decision(decision)
        
        return decisions
        
    except Exception as e:
        logger.log_error_explicit(e, f"analyze_symbol({symbol}, {timeframe})")
        
        # Write error to Airtable
        try:
            writer = AirtableWriter()
            writer.write_error_log(str(e), f"{symbol}_{timeframe}")
        except:
            pass  # Don't fail on error logging failure
        
        return []


def run_analysis_cycle(cycle_num: int = 1):
    """
    Run a single analysis cycle.
    
    Args:
        cycle_num: Cycle number
    """
    logger = get_logger()
    logger.log_cycle_start(cycle_num)
    
    # Initialize fetcher
    fetcher = MarketDataFetcher()
    
    # Statistics
    stats = {
        "symbols_analyzed": 0,
        "setups_detected": 0,
        "decisions_forming": 0,
        "decisions_rejected": 0,
    }
    
    all_decisions = []
    
    # Analyze each symbol/timeframe
    for symbol in SYMBOL_UNIVERSE:
        for timeframe in TIMEFRAMES:
            stats["symbols_analyzed"] += 1
            
            decisions = analyze_symbol(symbol, timeframe, logger, fetcher)
            
            for decision in decisions:
                stats["setups_detected"] += 1
                
                if decision.get("status") == "forming":
                    stats["decisions_forming"] += 1
                else:
                    stats["decisions_rejected"] += 1
                
                all_decisions.append(decision)
    
    # Write cycle log to Airtable
    logger.info(f"Writing cycle log to Airtable")
    try:
        write_cycle(cycle_num, stats)
        logger.log_airtable_write(TABLE_BRAIN_LOGS, success=True, details=f"Cycle {cycle_num}")
    except Exception as e:
        logger.log_error_explicit(e, "write_cycle")
        logger.log_airtable_write(TABLE_BRAIN_LOGS, success=False, details=str(e))
    
    # Write decisions to Airtable
    if all_decisions:
        logger.info(f"Writing {len(all_decisions)} decisions to Airtable")
        try:
            decision_stats = write_decisions(all_decisions)
            logger.info(f"Decisions written: {decision_stats['logged']} logged, {decision_stats['forming']} forming")
        except Exception as e:
            logger.log_error_explicit(e, "write_decisions")
    
    logger.log_cycle_end(cycle_num, stats)
    
    # Print summary
    print("\n" + "="*60)
    print(f"CYCLE {cycle_num} SUMMARY")
    print("="*60)
    print(f"Symbols analyzed: {stats['symbols_analyzed']}")
    print(f"Setups detected: {stats['setups_detected']}")
    print(f"Decisions FORMING: {stats['decisions_forming']}")
    print(f"Decisions REJECTED: {stats['decisions_rejected']}")
    print("="*60 + "\n")


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("Brain YAGATI v2 - Deterministic Decision Module")
    print("="*60 + "\n")
    
    logger = get_logger()
    logger.log_startup()
    
    # Write startup log to Airtable
    print("📡 Writing startup heartbeat to Airtable...")
    try:
        if write_startup():
            print("✅ Startup heartbeat logged to Airtable")
            logger.log_airtable_write(TABLE_BRAIN_LOGS, success=True, details="Startup")
        else:
            print("⚠️ Failed to write startup heartbeat")
            logger.log_airtable_write(TABLE_BRAIN_LOGS, success=False, details="Startup failed")
    except Exception as e:
        logger.log_error_explicit(e, "write_startup")
        print(f"❌ Error writing startup log: {e}")
    
    print(f"\n🔍 Starting analysis...")
    print(f"Symbol universe: {len(SYMBOL_UNIVERSE)} symbols")
    print(f"Timeframes: {', '.join(TIMEFRAMES)}")
    print(f"Total combinations: {len(SYMBOL_UNIVERSE) * len(TIMEFRAMES)}\n")
    
    # Run a single analysis cycle
    try:
        run_analysis_cycle(cycle_num=1)
    except Exception as e:
        logger.log_error_explicit(e, "run_analysis_cycle")
        print(f"\n❌ Error in analysis cycle: {e}")
        
        # Try to write error to Airtable
        try:
            writer = AirtableWriter()
            writer.write_error_log(str(e), "GLOBAL")
        except:
            pass
    
    print("\n✅ Brain YAGATI v2 execution complete")
    print("Check Airtable for results:")
    print(f"  - brain_logs: Startup, cycle, and decision logs")
    print(f"  - setups_forming: Detected forming setups (if any)\n")


if __name__ == "__main__":
    # Import TABLE names for display
    from brain_v2.config.settings import TABLE_BRAIN_LOGS
    main()
