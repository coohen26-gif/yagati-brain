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
    - Only logs when regime is TRANSITION (indicating a possible regime change in progress)
    - Only logs when EMA slope is extremely significant (>1.0% change)
    
    This ensures observations are sparse and only logged when something notable is happening.
    
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
            
            # Only log TRANSITION regime (indicating potential change in progress)
            # This makes observations sparse - only logged when regime is unclear
            if regime == "TRANSITION":
                note = "regime transition detected"
                if log_brain_observation(symbol, status="neutral", note=note):
                    success_count += 1
                    continue  # Don't double-log for the same symbol
            
            # Check for very significant EMA slope changes (conservative threshold)
            try:
                candles = fetch_ohlc(symbol, "1d", limit=30)
                closes = [float(c["close"]) for c in candles if c.get("close") is not None]
                
                if len(closes) >= 20:
                    slp = slope(closes, lookback=20)
                    if slp is not None:
                        slope_pct = slp * 100.0
                        
                        # Only log very significant slope changes (>1% is significant for 20-day slope)
                        if abs(slope_pct) >= 1.0:
                            if slope_pct > 0:
                                note = "strong upward momentum"
                            else:
                                note = "strong downward momentum"
                            
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
