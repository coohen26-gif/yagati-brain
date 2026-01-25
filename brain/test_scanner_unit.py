#!/usr/bin/env python3
"""
Unit tests for market scanner detection rules.
Tests the logic without requiring external API calls.
"""

import sys
import os


# Test data generators
def generate_low_volatility_candles(count=50):
    """Generate candles with low, stable volatility."""
    candles = []
    base_price = 100.0
    for i in range(count):
        price = base_price + (i * 0.1)  # Slow drift
        candles.append({
            'high': str(price + 0.5),
            'low': str(price - 0.5),
            'close': str(price),
            'open': str(price - 0.2)
        })
    return candles


def generate_volatility_expansion_candles(count=60):
    """Generate candles showing volatility expansion."""
    candles = []
    base_price = 100.0
    
    # First 45 candles: very low volatility (ensures clean baseline for candles[-30:-10])
    for i in range(45):
        price = base_price + (i * 0.05)
        candles.append({
            'high': str(price + 0.15),  # Very small range
            'low': str(price - 0.15),
            'close': str(price),
            'open': str(price - 0.03)
        })
    
    # Last 15 candles: very high volatility (for candles[-7:] to be very volatile)
    for i in range(15):
        price = base_price + 45 * 0.05 + (i * 0.1)
        candles.append({
            'high': str(price + 3.0),  # Much larger range
            'low': str(price - 3.0),
            'close': str(price),
            'open': str(price - 0.3)
        })
    
    return candles


def generate_trend_acceleration_candles(count=60):
    """Generate candles showing strong trend acceleration."""
    candles = []
    base_price = 100.0
    
    # Strong uptrend - price moves way above moving averages
    for i in range(count):
        # Accelerating price
        price = base_price + (i * i * 0.05)  # Quadratic growth
        candles.append({
            'high': str(price + 1.0),
            'low': str(price - 0.5),
            'close': str(price),
            'open': str(price - 0.3)
        })
    
    return candles


def generate_compression_expansion_candles(count=50):
    """Generate candles showing compression then expansion."""
    candles = []
    base_price = 100.0
    
    # Indices 0-19: Initial candles (not sampled, can be anything)
    for i in range(20):
        price = base_price + (i * 0.1)
        candles.append({
            'high': str(price + 0.5),
            'low': str(price - 0.5),
            'close': str(price),
            'open': str(price - 0.1)
        })
    
    # Indices 20-34: NORMAL volatility (15 candles for old_vol baseline)
    for i in range(15):
        price = base_price + 20 * 0.1 + (i * 0.1)
        candles.append({
            'high': str(price + 1.0),  # Normal range
            'low': str(price - 1.0),
            'close': str(price),
            'open': str(price - 0.2)
        })
    
    # Indices 35-44: COMPRESSED volatility (10 candles for mid_vol)
    for i in range(10):
        price = base_price + 20 * 0.1 + 15 * 0.1 + (i * 0.02)
        candles.append({
            'high': str(price + 0.15),  # Very small range (15% of normal)
            'low': str(price - 0.15),
            'close': str(price),
            'open': str(price - 0.03)
        })
    
    # Indices 45-49: EXPANDED volatility (5 candles for current_vol)
    for i in range(5):
        price = base_price + 20 * 0.1 + 15 * 0.1 + 10 * 0.02 + (i * 0.2)
        candles.append({
            'high': str(price + 3.0),  # Large range (20x compressed, 3x normal)
            'low': str(price - 3.0),
            'close': str(price),
            'open': str(price - 0.4)
        })
    
    return candles


# Import detection functions (inline to avoid env var issues)
def calculate_atr_proxy(candles, period=14):
    """Calculate ATR proxy."""
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
    """Calculate volatility percentage."""
    atr = calculate_atr_proxy(candles, period)
    if atr is None:
        return None
    if not candles:
        return None
    current_price = float(candles[-1].get("close", 0))
    if current_price == 0:
        return None
    return (atr / current_price) * 100.0


def test_volatility_expansion_detection():
    """Test volatility expansion detection."""
    print("\n" + "=" * 50)
    print("Test 1: Volatility Expansion Detection")
    print("=" * 50)
    
    candles = generate_volatility_expansion_candles()
    
    # Calculate current vs average volatility
    current_vol = calculate_volatility_pct(candles[-7:], period=7)
    avg_vol = calculate_volatility_pct(candles[-30:-10], period=20)
    
    print(f"Current volatility: {current_vol:.2f}%")
    print(f"Average volatility: {avg_vol:.2f}%")
    print(f"Ratio: {current_vol / avg_vol:.2f}x")
    
    if current_vol > 2.0 * avg_vol:
        print("✅ PASS: Volatility expansion detected (>2x)")
        return True
    else:
        print("❌ FAIL: Should detect volatility expansion")
        return False


def test_no_false_positives():
    """Test that low volatility doesn't trigger detection."""
    print("\n" + "=" * 50)
    print("Test 2: No False Positives (Low Volatility)")
    print("=" * 50)
    
    candles = generate_low_volatility_candles()
    
    current_vol = calculate_volatility_pct(candles[-7:], period=7)
    avg_vol = calculate_volatility_pct(candles[-30:-10], period=20)
    
    print(f"Current volatility: {current_vol:.2f}%")
    print(f"Average volatility: {avg_vol:.2f}%")
    print(f"Ratio: {current_vol / avg_vol:.2f}x")
    
    if current_vol <= 2.0 * avg_vol:
        print("✅ PASS: No false positive (stable volatility)")
        return True
    else:
        print("❌ FAIL: Should NOT detect expansion in stable market")
        return False


def test_compression_expansion_detection():
    """Test compression → expansion detection."""
    print("\n" + "=" * 50)
    print("Test 3: Compression → Expansion Detection")
    print("=" * 50)
    
    candles = generate_compression_expansion_candles()
    
    old_vol = calculate_volatility_pct(candles[-30:-15], period=15)
    mid_vol = calculate_volatility_pct(candles[-15:-5], period=10)
    current_vol = calculate_volatility_pct(candles[-5:], period=5)
    
    print(f"Old volatility: {old_vol:.2f}%")
    print(f"Mid volatility (compressed): {mid_vol:.2f}%")
    print(f"Current volatility (expanded): {current_vol:.2f}%")
    
    compression = mid_vol < old_vol * 0.7
    expansion = current_vol > mid_vol * 1.5
    
    print(f"Compression detected: {compression}")
    print(f"Expansion detected: {expansion}")
    
    if compression and expansion:
        print("✅ PASS: Compression → expansion pattern detected")
        return True
    else:
        print("❌ FAIL: Should detect squeeze release pattern")
        return False


def test_calculations_with_edge_cases():
    """Test calculations handle edge cases."""
    print("\n" + "=" * 50)
    print("Test 4: Edge Cases")
    print("=" * 50)
    
    # Empty candles
    vol = calculate_volatility_pct([], period=14)
    if vol is None:
        print("✅ PASS: Handles empty candles")
    else:
        print("❌ FAIL: Should return None for empty candles")
        return False
    
    # Insufficient data
    short_candles = generate_low_volatility_candles(5)
    vol = calculate_volatility_pct(short_candles, period=14)
    if vol is None:
        print("✅ PASS: Handles insufficient data")
    else:
        print("❌ FAIL: Should return None for insufficient data")
        return False
    
    # Valid data
    candles = generate_low_volatility_candles(30)
    vol = calculate_volatility_pct(candles, period=14)
    if vol is not None and vol > 0:
        print(f"✅ PASS: Calculates volatility ({vol:.2f}%) with valid data")
        return True
    else:
        print("❌ FAIL: Should calculate volatility with valid data")
        return False


def main():
    """Run all unit tests."""
    print("=" * 50)
    print("Market Scanner Unit Tests")
    print("=" * 50)
    print("\nTesting detection logic with synthetic data...")
    
    results = []
    
    results.append(test_volatility_expansion_detection())
    results.append(test_no_false_positives())
    results.append(test_compression_expansion_detection())
    results.append(test_calculations_with_edge_cases())
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL UNIT TESTS PASSED!")
        print("\nDetection logic is working correctly.")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
