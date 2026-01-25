"""
Market Scanner Module (V1.1.3-01)

Scans crypto markets for early trading setups without executing trades.
Uses simple, explainable metrics only (NO ML/AI).

Detects:
- Volatility expansion
- Range breakouts
- Trend acceleration
- Compression → expansion patterns
"""

import os
import sys
from datetime import datetime, timezone

# Add brain directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from market_regime import fetch_ohlc, ema, slope


# Market universe (top market cap crypto assets)
MARKET_UNIVERSE = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT"]

# Timeframes to scan
TIMEFRAMES = ["1h", "4h", "1d"]


def calculate_atr_proxy(candles, period=14):
    """
    Calculate ATR proxy (average true range) as a volatility measure.
    Uses high-low range as a simple approximation.
    
    Args:
        candles: List of OHLC candles
        period: Period for ATR calculation (default 14)
        
    Returns:
        float: ATR proxy value or None if insufficient data
    """
    if len(candles) < period:
        return None
    
    ranges = []
    for candle in candles[-period:]:
        high = float(candle.get("high", 0))
        low = float(candle.get("low", 0))
        ranges.append(high - low)
    
    if not ranges:
        return None
    
    return sum(ranges) / len(ranges)


def calculate_volatility_pct(candles, period=14):
    """
    Calculate recent volatility as percentage of price.
    
    Args:
        candles: List of OHLC candles
        period: Period for calculation
        
    Returns:
        float: Volatility percentage or None
    """
    atr = calculate_atr_proxy(candles, period)
    if atr is None:
        return None
    
    # Get current price
    if not candles:
        return None
    
    current_price = float(candles[-1].get("close", 0))
    if current_price == 0:
        return None
    
    return (atr / current_price) * 100.0


def calculate_price_change_pct(candles, lookback=10):
    """
    Calculate price change over last N candles.
    
    Args:
        candles: List of OHLC candles
        lookback: Number of candles to look back
        
    Returns:
        float: Price change percentage or None
    """
    if len(candles) < lookback + 1:
        return None
    
    start_price = float(candles[-lookback - 1].get("close", 0))
    end_price = float(candles[-1].get("close", 0))
    
    if start_price == 0:
        return None
    
    return ((end_price - start_price) / start_price) * 100.0


def calculate_ma_distance(candles, ma_period=20):
    """
    Calculate distance from price to moving average.
    
    Args:
        candles: List of OHLC candles
        ma_period: MA period (20 or 50)
        
    Returns:
        float: Distance percentage or None
    """
    if len(candles) < ma_period:
        return None
    
    closes = [float(c["close"]) for c in candles if c.get("close") is not None]
    
    if len(closes) < ma_period:
        return None
    
    ma_value = ema(closes, ma_period)
    if ma_value is None:
        return None
    
    current_price = closes[-1]
    if current_price == 0:
        return None
    
    return ((current_price - ma_value) / ma_value) * 100.0


def calculate_proximity_to_extremes(candles, lookback=20):
    """
    Calculate proximity to recent high/low.
    
    Args:
        candles: List of OHLC candles
        lookback: Period to find high/low
        
    Returns:
        dict: {distance_to_high_pct, distance_to_low_pct} or None
    """
    if len(candles) < lookback:
        return None
    
    recent_candles = candles[-lookback:]
    
    highs = [float(c.get("high", 0)) for c in recent_candles]
    lows = [float(c.get("low", 0)) for c in recent_candles]
    
    if not highs or not lows:
        return None
    
    recent_high = max(highs)
    recent_low = min(lows)
    
    current_price = float(candles[-1].get("close", 0))
    
    if current_price == 0:
        return None
    
    dist_to_high = ((recent_high - current_price) / current_price) * 100.0
    dist_to_low = ((current_price - recent_low) / current_price) * 100.0
    
    return {
        "distance_to_high_pct": dist_to_high,
        "distance_to_low_pct": dist_to_low
    }


def detect_volatility_expansion(candles):
    """
    Detect volatility expansion: current volatility > 2x recent average.
    
    Returns:
        dict: Setup info or None
    """
    if len(candles) < 30:
        return None
    
    # Current volatility (last 7 periods)
    current_vol = calculate_volatility_pct(candles[-7:], period=7)
    
    # Average volatility (20-30 periods back)
    avg_vol = calculate_volatility_pct(candles[-30:-10], period=20)
    
    if current_vol is None or avg_vol is None or avg_vol == 0:
        return None
    
    # Volatility expansion detected
    if current_vol > 2.0 * avg_vol:
        confidence = "HIGH" if current_vol > 3.0 * avg_vol else "MEDIUM"
        return {
            "setup_type": "volatility_expansion",
            "confidence": confidence,
            "context": f"current_vol={current_vol:.2f}% vs avg={avg_vol:.2f}%"
        }
    
    return None


def detect_range_break_attempt(candles):
    """
    Detect range break attempt: price near recent high/low with expansion.
    
    Returns:
        dict: Setup info or None
    """
    if len(candles) < 30:
        return None
    
    proximity = calculate_proximity_to_extremes(candles, lookback=20)
    if proximity is None:
        return None
    
    current_vol = calculate_volatility_pct(candles[-7:], period=7)
    avg_vol = calculate_volatility_pct(candles[-30:-10], period=20)
    
    if current_vol is None or avg_vol is None or avg_vol == 0:
        return None
    
    # Check if near high or low (within 2%)
    near_high = proximity["distance_to_high_pct"] < 2.0
    near_low = proximity["distance_to_low_pct"] < 2.0
    
    # Check if volatility is expanding
    vol_expanding = current_vol > 1.5 * avg_vol
    
    if (near_high or near_low) and vol_expanding:
        direction = "upside" if near_high else "downside"
        confidence = "MEDIUM" if vol_expanding else "LOW"
        return {
            "setup_type": "range_break_attempt",
            "confidence": confidence,
            "context": f"{direction} break attempt, vol expanding"
        }
    
    return None


def detect_trend_acceleration(candles):
    """
    Detect trend acceleration: price extended abnormally from MA.
    
    Returns:
        dict: Setup info or None
    """
    if len(candles) < 50:
        return None
    
    # Check distance from MA20 and MA50
    ma20_dist = calculate_ma_distance(candles, ma_period=20)
    ma50_dist = calculate_ma_distance(candles, ma_period=50)
    
    if ma20_dist is None or ma50_dist is None:
        return None
    
    # Extended from MA20 (>5%) or MA50 (>8%)
    extended_ma20 = abs(ma20_dist) > 5.0
    extended_ma50 = abs(ma50_dist) > 8.0
    
    if extended_ma20 or extended_ma50:
        direction = "up" if ma20_dist > 0 else "down"
        confidence = "HIGH" if extended_ma50 else "MEDIUM"
        return {
            "setup_type": "trend_acceleration",
            "confidence": confidence,
            "context": f"extended {direction}, ma20_dist={ma20_dist:.1f}%, ma50_dist={ma50_dist:.1f}%"
        }
    
    return None


def detect_compression_expansion(candles):
    """
    Detect compression → expansion: low range followed by sudden expansion.
    
    Returns:
        dict: Setup info or None
    """
    if len(candles) < 30:
        return None
    
    # Calculate volatility for different periods
    old_vol = calculate_volatility_pct(candles[-30:-15], period=15)
    mid_vol = calculate_volatility_pct(candles[-15:-5], period=10)
    current_vol = calculate_volatility_pct(candles[-5:], period=5)
    
    if old_vol is None or mid_vol is None or current_vol is None:
        return None
    
    if old_vol == 0:
        return None
    
    # Compression: mid_vol < old_vol
    compression = mid_vol < old_vol * 0.7
    
    # Expansion: current_vol > mid_vol
    expansion = current_vol > mid_vol * 1.5
    
    if compression and expansion:
        confidence = "HIGH" if current_vol > mid_vol * 2.0 else "MEDIUM"
        return {
            "setup_type": "compression_expansion",
            "confidence": confidence,
            "context": f"squeeze release, vol: {mid_vol:.2f}% → {current_vol:.2f}%"
        }
    
    return None


def scan_symbol_timeframe(symbol, timeframe):
    """
    Scan a single symbol on a single timeframe for setups.
    
    Args:
        symbol: Market symbol (e.g., "BTCUSDT")
        timeframe: Timeframe string (e.g., "1h", "4h", "1d")
        
    Returns:
        list: List of detected setups (dicts)
    """
    setups = []
    
    try:
        # Fetch OHLC data
        candles = fetch_ohlc(symbol, timeframe, limit=100)
        
        if not candles or len(candles) < 30:
            return setups
        
        # Run all detection rules
        detectors = [
            detect_volatility_expansion,
            detect_range_break_attempt,
            detect_trend_acceleration,
            detect_compression_expansion
        ]
        
        for detector in detectors:
            setup = detector(candles)
            if setup:
                # Add symbol and timeframe info
                setup["symbol"] = symbol
                setup["timeframe"] = timeframe
                setup["status"] = "FORMING"
                setup["detected_at"] = datetime.now(timezone.utc).isoformat()
                setups.append(setup)
        
    except Exception as e:
        print(f"⚠️ Error scanning {symbol} {timeframe}: {e}")
    
    return setups


def scan_all_markets():
    """
    Scan all symbols across all timeframes.
    
    Returns:
        list: All detected setups
    """
    all_setups = []
    
    print("\n🔍 Starting market scan...")
    
    for symbol in MARKET_UNIVERSE:
        for timeframe in TIMEFRAMES:
            setups = scan_symbol_timeframe(symbol, timeframe)
            all_setups.extend(setups)
            
            if setups:
                print(f"  ✓ {symbol} {timeframe}: {len(setups)} setup(s) detected")
    
    print(f"✅ Market scan complete: {len(all_setups)} total setup(s) detected")
    
    return all_setups


if __name__ == "__main__":
    """
    Test the market scanner directly.
    """
    print("=" * 50)
    print("Market Scanner Test")
    print("=" * 50)
    
    setups = scan_all_markets()
    
    print("\n" + "=" * 50)
    print("Detected Setups:")
    print("=" * 50)
    
    for setup in setups:
        print(f"\n{setup['symbol']} {setup['timeframe']} - {setup['setup_type']}")
        print(f"  Confidence: {setup['confidence']}")
        print(f"  Context: {setup['context']}")
        print(f"  Status: {setup['status']}")
        print(f"  Detected: {setup['detected_at']}")
