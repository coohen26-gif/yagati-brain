"""
Brain Cognitive Events Module (YAGATI-BRAIN-002)

This module handles cognitive event generation for the YAGATI brain:
- Market scanning events
- Pattern observation events (conservative and sparse)

Events are logged to Airtable brain_logs table with cycle_type "scan" or "observation".
"""

import os
import sys

# Add brain directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from airtable_logger import log_brain_scan, log_brain_observation
from market_regime import detect_regime, slope, fetch_ohlc


# Symbols to monitor (common markets the brain already monitors)
MONITORED_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


def log_scan_events():
    """
    Generate and log scan events for each monitored symbol.
    A scan event indicates the brain is reading market data for that symbol.
    
    Returns:
        int: Number of successful scan events logged
    """
    success_count = 0
    
    for symbol in MONITORED_SYMBOLS:
        try:
            # Log scan event
            if log_brain_scan(symbol):
                success_count += 1
        except Exception as e:
            print(f"⚠️ Failed to log scan event for {symbol}: {e}")
    
    return success_count


def detect_observations():
    """
    Detect and log observation events for monitored symbols.
    
    Observations are conservative and sparse:
    - Regime transitions (RANGE -> TREND, TREND -> RANGE, etc.)
    - Significant EMA slope changes
    
    Returns:
        int: Number of successful observation events logged
    """
    success_count = 0
    
    for symbol in MONITORED_SYMBOLS:
        try:
            # Detect regime
            regime_data = detect_regime(symbol)
            regime = regime_data.get("regime")
            bias = regime_data.get("bias")
            
            # Check for regime transition (conservative detection)
            # Only log if regime is clearly defined (not TRANSITION)
            if regime == "TREND" and bias:
                # Log trend observation
                note = f"trend regime detected ({bias})"
                if log_brain_observation(symbol, status="neutral", note=note):
                    success_count += 1
            
            elif regime == "RANGE":
                # Log range observation
                note = "range regime detected"
                if log_brain_observation(symbol, status="neutral", note=note):
                    success_count += 1
            
            # Check for significant EMA slope changes (additional conservative check)
            try:
                candles = fetch_ohlc(symbol, "1d", limit=30)
                closes = [float(c["close"]) for c in candles if c.get("close") is not None]
                
                if len(closes) >= 20:
                    slp = slope(closes, lookback=20)
                    if slp is not None:
                        slope_pct = slp * 100.0
                        
                        # Only log significant slope changes
                        if abs(slope_pct) >= 0.5:  # 0.5% or more slope
                            if slope_pct > 0:
                                note = "significant upward momentum"
                            else:
                                note = "significant downward momentum"
                            
                            if log_brain_observation(symbol, status="weak", note=note):
                                success_count += 1
            
            except Exception as e:
                # Silently skip slope check if it fails
                pass
                
        except Exception as e:
            print(f"⚠️ Failed to detect observations for {symbol}: {e}")
    
    return success_count


def log_cognitive_events():
    """
    Main function to orchestrate cognitive event logging.
    
    This function:
    1. Logs scan events for all monitored symbols
    2. Detects and logs observation events (sparse and conservative)
    
    This is designed to be called from the brain loop.
    Fails gracefully if anything goes wrong.
    """
    try:
        print("\n🔍 Logging cognitive events...")
        
        # Log scan events
        scan_count = log_scan_events()
        print(f"✅ Logged {scan_count} scan events")
        
        # Detect and log observations (conservative)
        observation_count = detect_observations()
        print(f"✅ Logged {observation_count} observation events")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Cognitive events logging failed (non-blocking): {e}")
        return False


if __name__ == "__main__":
    """
    Test the cognitive events module directly.
    """
    print("=" * 50)
    print("YAGATI-BRAIN-002 Cognitive Events Test")
    print("=" * 50)
    
    log_cognitive_events()
