"""
Paper Trading Module - MFE/MAE and Water Marks Test

Tests the new MFE/MAE calculations and water mark tracking.
"""

import sys
import os

# Set mock environment variables for testing
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test_key"
os.environ["AIRTABLE_API_KEY"] = "test_key"
os.environ["AIRTABLE_BASE_ID"] = "test_base"

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain_v2.paper_trading.position import PositionCalculator


def test_water_mark_updates_long():
    """Test water mark updates for LONG positions"""
    print("\n" + "="*60)
    print("Test 1: Water Mark Updates - LONG")
    print("="*60)
    
    calculator = PositionCalculator()
    
    # Initial state
    entry_price = 50000.0
    high_water = entry_price
    low_water = entry_price
    
    print(f"\n📊 Initial: Entry={entry_price}, High={high_water}, Low={low_water}")
    
    # Price goes up
    current_price = 51000.0
    result = calculator.update_water_marks(current_price, high_water, low_water, "LONG")
    high_water = result["high_water_mark"]
    low_water = result["low_water_mark"]
    
    print(f"   Price up to {current_price}: High={high_water}, Low={low_water}")
    assert high_water == 51000.0, "High water mark should increase"
    assert low_water == 50000.0, "Low water mark should stay same"
    
    # Price goes down
    current_price = 49500.0
    result = calculator.update_water_marks(current_price, high_water, low_water, "LONG")
    high_water = result["high_water_mark"]
    low_water = result["low_water_mark"]
    
    print(f"   Price down to {current_price}: High={high_water}, Low={low_water}")
    assert high_water == 51000.0, "High water mark should stay same"
    assert low_water == 49500.0, "Low water mark should decrease"
    
    # Price goes even higher
    current_price = 52000.0
    result = calculator.update_water_marks(current_price, high_water, low_water, "LONG")
    high_water = result["high_water_mark"]
    low_water = result["low_water_mark"]
    
    print(f"   Price up to {current_price}: High={high_water}, Low={low_water}")
    assert high_water == 52000.0, "High water mark should increase again"
    assert low_water == 49500.0, "Low water mark should stay same"
    
    print("   ✅ All water mark updates correct for LONG")
    return True


def test_water_mark_updates_short():
    """Test water mark updates for SHORT positions"""
    print("\n" + "="*60)
    print("Test 2: Water Mark Updates - SHORT")
    print("="*60)
    
    calculator = PositionCalculator()
    
    # Initial state
    entry_price = 3000.0
    high_water = entry_price
    low_water = entry_price
    
    print(f"\n📊 Initial: Entry={entry_price}, High={high_water}, Low={low_water}")
    
    # Price goes down (favorable for SHORT)
    current_price = 2900.0
    result = calculator.update_water_marks(current_price, high_water, low_water, "SHORT")
    high_water = result["high_water_mark"]
    low_water = result["low_water_mark"]
    
    print(f"   Price down to {current_price}: High={high_water}, Low={low_water}")
    assert low_water == 2900.0, "Low water mark should decrease"
    assert high_water == 3000.0, "High water mark should stay same"
    
    # Price goes up (adverse for SHORT)
    current_price = 3100.0
    result = calculator.update_water_marks(current_price, high_water, low_water, "SHORT")
    high_water = result["high_water_mark"]
    low_water = result["low_water_mark"]
    
    print(f"   Price up to {current_price}: High={high_water}, Low={low_water}")
    assert high_water == 3100.0, "High water mark should increase"
    assert low_water == 2900.0, "Low water mark should stay same"
    
    # Price goes even lower (more favorable)
    current_price = 2800.0
    result = calculator.update_water_marks(current_price, high_water, low_water, "SHORT")
    high_water = result["high_water_mark"]
    low_water = result["low_water_mark"]
    
    print(f"   Price down to {current_price}: High={high_water}, Low={low_water}")
    assert low_water == 2800.0, "Low water mark should decrease again"
    assert high_water == 3100.0, "High water mark should stay same"
    
    print("   ✅ All water mark updates correct for SHORT")
    return True


def test_mfe_mae_long():
    """Test MFE/MAE calculations for LONG positions"""
    print("\n" + "="*60)
    print("Test 3: MFE/MAE Calculation - LONG")
    print("="*60)
    
    calculator = PositionCalculator()
    
    # LONG trade scenario:
    # Entry: 50000
    # High water mark: 52000 (went up 4%)
    # Low water mark: 49000 (went down 2%)
    entry_price = 50000.0
    high_water = 52000.0
    low_water = 49000.0
    
    result = calculator.calculate_mfe_mae(entry_price, high_water, low_water, "LONG")
    mfe = result["mfe_percent"]
    mae = result["mae_percent"]
    
    print(f"\n📊 LONG Trade Analysis:")
    print(f"   Entry: {entry_price}")
    print(f"   High Water: {high_water} (+{((high_water - entry_price) / entry_price * 100):.2f}%)")
    print(f"   Low Water: {low_water} ({((low_water - entry_price) / entry_price * 100):.2f}%)")
    print(f"   MFE: {mfe:+.2f}%")
    print(f"   MAE: {mae:+.2f}%")
    
    assert abs(mfe - 4.0) < 0.01, f"MFE should be +4%, got {mfe}"
    assert abs(mae - (-2.0)) < 0.01, f"MAE should be -2%, got {mae}"
    print("   ✅ MFE/MAE calculations correct for LONG")
    
    return True


def test_mfe_mae_short():
    """Test MFE/MAE calculations for SHORT positions"""
    print("\n" + "="*60)
    print("Test 4: MFE/MAE Calculation - SHORT")
    print("="*60)
    
    calculator = PositionCalculator()
    
    # SHORT trade scenario:
    # Entry: 3000
    # Low water mark: 2800 (went down 6.67% - favorable)
    # High water mark: 3100 (went up 3.33% - adverse)
    entry_price = 3000.0
    low_water = 2800.0
    high_water = 3100.0
    
    result = calculator.calculate_mfe_mae(entry_price, high_water, low_water, "SHORT")
    mfe = result["mfe_percent"]
    mae = result["mae_percent"]
    
    print(f"\n📊 SHORT Trade Analysis:")
    print(f"   Entry: {entry_price}")
    print(f"   Low Water: {low_water} ({((low_water - entry_price) / entry_price * 100):.2f}%)")
    print(f"   High Water: {high_water} (+{((high_water - entry_price) / entry_price * 100):.2f}%)")
    print(f"   MFE: {mfe:+.2f}%")
    print(f"   MAE: {mae:+.2f}%")
    
    expected_mfe = ((entry_price - low_water) / entry_price) * 100
    expected_mae = ((entry_price - high_water) / entry_price) * 100
    
    assert abs(mfe - expected_mfe) < 0.01, f"MFE should be {expected_mfe:.2f}%, got {mfe}"
    assert abs(mae - expected_mae) < 0.01, f"MAE should be {expected_mae:.2f}%, got {mae}"
    print("   ✅ MFE/MAE calculations correct for SHORT")
    
    return True


def test_mfe_mae_winning_long():
    """Test MFE/MAE for winning LONG trade"""
    print("\n" + "="*60)
    print("Test 5: MFE/MAE - Winning LONG Trade")
    print("="*60)
    
    calculator = PositionCalculator()
    
    # Winning LONG trade that hit TP
    # Entry: 50000, TP: 52000 (hit)
    # High: 52000 (TP hit), Low: 49500 (small drawdown)
    entry_price = 50000.0
    high_water = 52000.0  # Hit TP
    low_water = 49500.0   # Small drawdown
    
    result = calculator.calculate_mfe_mae(entry_price, high_water, low_water, "LONG")
    mfe = result["mfe_percent"]
    mae = result["mae_percent"]
    
    print(f"\n📊 Winning LONG (TP Hit):")
    print(f"   Entry: {entry_price} → Exit: {high_water} (TP)")
    print(f"   MFE: {mfe:+.2f}% (favorable move)")
    print(f"   MAE: {mae:+.2f}% (adverse move)")
    
    assert mfe > 0, "MFE should be positive for winning trade"
    assert mae < 0, "MAE should be negative (drawdown)"
    print("   ✅ MFE positive, MAE negative as expected")
    
    return True


def test_mfe_mae_losing_long():
    """Test MFE/MAE for losing LONG trade"""
    print("\n" + "="*60)
    print("Test 6: MFE/MAE - Losing LONG Trade")
    print("="*60)
    
    calculator = PositionCalculator()
    
    # Losing LONG trade that hit SL
    # Entry: 50000, SL: 49000 (hit)
    # High: 50500 (small profit first), Low: 49000 (SL hit)
    entry_price = 50000.0
    high_water = 50500.0  # Small profit before losing
    low_water = 49000.0   # Hit SL
    
    result = calculator.calculate_mfe_mae(entry_price, high_water, low_water, "LONG")
    mfe = result["mfe_percent"]
    mae = result["mae_percent"]
    
    print(f"\n📊 Losing LONG (SL Hit):")
    print(f"   Entry: {entry_price} → Exit: {low_water} (SL)")
    print(f"   MFE: {mfe:+.2f}% (best point reached)")
    print(f"   MAE: {mae:+.2f}% (worst point - SL)")
    
    assert mfe > 0, "MFE should be positive (trade went in favor briefly)"
    assert mae < 0, "MAE should be negative (hit SL)"
    assert abs(mae) > abs(mfe), "MAE magnitude should be larger (lost more than gained)"
    print("   ✅ MFE shows brief profit, MAE shows larger loss")
    
    return True


def test_rsi_calculation():
    """Test RSI calculation from technical features"""
    print("\n" + "="*60)
    print("Test 7: RSI Calculation")
    print("="*60)
    
    from brain_v2.features.technical import calculate_rsi
    
    # Create simple price sequence
    # Uptrend: should have RSI > 50
    uptrend_candles = []
    base_price = 100.0
    for i in range(20):
        price = base_price + i * 0.5  # Steady uptrend
        uptrend_candles.append({
            "open": price,
            "high": price + 0.5,
            "low": price - 0.3,
            "close": price + 0.4
        })
    
    rsi_up = calculate_rsi(uptrend_candles, period=14)
    print(f"\n📊 Uptrend RSI: {rsi_up:.2f}")
    assert rsi_up is not None, "RSI should be calculated"
    assert rsi_up > 50, f"Uptrend RSI should be > 50, got {rsi_up}"
    print("   ✅ Uptrend RSI > 50")
    
    # Downtrend: should have RSI < 50
    downtrend_candles = []
    base_price = 100.0
    for i in range(20):
        price = base_price - i * 0.5  # Steady downtrend
        downtrend_candles.append({
            "open": price,
            "high": price + 0.3,
            "low": price - 0.5,
            "close": price - 0.4
        })
    
    rsi_down = calculate_rsi(downtrend_candles, period=14)
    print(f"📊 Downtrend RSI: {rsi_down:.2f}")
    assert rsi_down is not None, "RSI should be calculated"
    assert rsi_down < 50, f"Downtrend RSI should be < 50, got {rsi_down}"
    print("   ✅ Downtrend RSI < 50")
    
    return True


def test_market_regime_detection():
    """Test market regime detection"""
    print("\n" + "="*60)
    print("Test 8: Market Regime Detection")
    print("="*60)
    
    from brain_v2.features.technical import determine_market_regime
    
    # Strong uptrend (need 200+ candles for MA_TREND=200)
    bull_candles = []
    for i in range(250):
        price = 1000 + i * 10  # Strong uptrend
        bull_candles.append({
            "open": price,
            "high": price + 5,
            "low": price - 3,
            "close": price + 4
        })
    
    regime = determine_market_regime(bull_candles)
    print(f"\n📊 Strong uptrend regime: {regime}")
    assert regime == "BULL", f"Should detect BULL, got {regime}"
    print("   ✅ Bull market detected")
    
    # Strong downtrend
    bear_candles = []
    for i in range(250):
        price = 2000 - i * 10  # Strong downtrend
        bear_candles.append({
            "open": price,
            "high": price + 3,
            "low": price - 5,
            "close": price - 4
        })
    
    regime = determine_market_regime(bear_candles)
    print(f"📊 Strong downtrend regime: {regime}")
    assert regime == "BEAR", f"Should detect BEAR, got {regime}"
    print("   ✅ Bear market detected")
    
    # Sideways
    sideways_candles = []
    for i in range(250):
        price = 1500 + (i % 5) * 2  # Oscillating
        sideways_candles.append({
            "open": price,
            "high": price + 1,
            "low": price - 1,
            "close": price
        })
    
    regime = determine_market_regime(sideways_candles)
    print(f"📊 Sideways market regime: {regime}")
    assert regime == "SIDEWAYS", f"Should detect SIDEWAYS, got {regime}"
    print("   ✅ Sideways market detected")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Paper Trading - MFE/MAE and Water Marks Tests")
    print("="*60)
    
    tests = [
        ("Water Mark Updates - LONG", test_water_mark_updates_long),
        ("Water Mark Updates - SHORT", test_water_mark_updates_short),
        ("MFE/MAE Calculation - LONG", test_mfe_mae_long),
        ("MFE/MAE Calculation - SHORT", test_mfe_mae_short),
        ("MFE/MAE - Winning LONG", test_mfe_mae_winning_long),
        ("MFE/MAE - Losing LONG", test_mfe_mae_losing_long),
        ("RSI Calculation", test_rsi_calculation),
        ("Market Regime Detection", test_market_regime_detection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60 + "\n")
    
    if passed == total:
        print("🎉 All tests passed!\n")
        return 0
    else:
        print("⚠️ Some tests failed\n")
        return 1


if __name__ == "__main__":
    exit(main())
