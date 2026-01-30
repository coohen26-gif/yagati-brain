"""
Paper Trading Module - Integration Test

Tests the paper trading module without requiring real Airtable credentials.
Validates the logic and data flow of all components.
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
from brain_v2.paper_trading.account import PaperAccount


def test_position_calculator():
    """Test position sizing calculations"""
    print("\n" + "="*60)
    print("Test 1: Position Calculator")
    print("="*60)
    
    calculator = PositionCalculator(risk_percent=0.01, rr_ratio=2.0)
    
    # Test LONG position
    print("\n📊 Testing LONG position calculation...")
    result = calculator.calculate_position_with_price(
        symbol="BTCUSDT",
        direction="LONG",
        entry_price=50000.0,
        stop_loss=49000.0,
        equity=100000.0
    )
    
    if result:
        print(f"✅ Position calculated:")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Direction: {result['direction']}")
        print(f"   Entry: {result['entry_price']:.2f}")
        print(f"   Position Size: {result['position_size']:.4f}")
        print(f"   Stop Loss: {result['stop_loss']:.2f}")
        print(f"   Take Profit: {result['take_profit']:.2f}")
        print(f"   Risk Amount: {result['risk_amount']:.2f} USDT (1%)")
        
        # Verify calculations
        assert result['risk_amount'] == 1000.0, "Risk should be 1% of equity"
        assert result['position_size'] == 1.0, "Position size should be 1.0"
        assert result['take_profit'] == 52000.0, "TP should be at 52000 (1:2 RR)"
        print("   ✅ All assertions passed")
    else:
        print("❌ Position calculation failed")
        return False
    
    # Test SHORT position
    print("\n📊 Testing SHORT position calculation...")
    result = calculator.calculate_position_with_price(
        symbol="ETHUSDT",
        direction="SHORT",
        entry_price=3000.0,
        stop_loss=3100.0,
        equity=100000.0
    )
    
    if result:
        print(f"✅ Position calculated:")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Direction: {result['direction']}")
        print(f"   Entry: {result['entry_price']:.2f}")
        print(f"   Position Size: {result['position_size']:.4f}")
        print(f"   Stop Loss: {result['stop_loss']:.2f}")
        print(f"   Take Profit: {result['take_profit']:.2f}")
        print(f"   Risk Amount: {result['risk_amount']:.2f} USDT (1%)")
        
        # Verify calculations
        assert result['risk_amount'] == 1000.0, "Risk should be 1% of equity"
        assert result['position_size'] == 10.0, "Position size should be 10.0"
        assert result['take_profit'] == 2800.0, "TP should be at 2800 (1:2 RR)"
        print("   ✅ All assertions passed")
    else:
        print("❌ Position calculation failed")
        return False
    
    return True


def test_sl_tp_checking():
    """Test SL/TP hit detection"""
    print("\n" + "="*60)
    print("Test 2: SL/TP Hit Detection")
    print("="*60)
    
    calculator = PositionCalculator()
    
    # Test LONG TP hit
    print("\n📊 Testing LONG TP hit...")
    result = calculator.check_sl_tp_hit(
        current_price=52000.0,
        direction="LONG",
        stop_loss=49000.0,
        take_profit=52000.0
    )
    assert result == "TP_HIT", "Should detect TP hit"
    print(f"✅ TP hit detected correctly: {result}")
    
    # Test LONG SL hit
    print("\n📊 Testing LONG SL hit...")
    result = calculator.check_sl_tp_hit(
        current_price=49000.0,
        direction="LONG",
        stop_loss=49000.0,
        take_profit=52000.0
    )
    assert result == "SL_HIT", "Should detect SL hit"
    print(f"✅ SL hit detected correctly: {result}")
    
    # Test SHORT TP hit
    print("\n📊 Testing SHORT TP hit...")
    result = calculator.check_sl_tp_hit(
        current_price=2800.0,
        direction="SHORT",
        stop_loss=3100.0,
        take_profit=2800.0
    )
    assert result == "TP_HIT", "Should detect TP hit"
    print(f"✅ TP hit detected correctly: {result}")
    
    # Test SHORT SL hit
    print("\n📊 Testing SHORT SL hit...")
    result = calculator.check_sl_tp_hit(
        current_price=3100.0,
        direction="SHORT",
        stop_loss=3100.0,
        take_profit=2800.0
    )
    assert result == "SL_HIT", "Should detect SL hit"
    print(f"✅ SL hit detected correctly: {result}")
    
    # Test no hit
    print("\n📊 Testing no hit...")
    result = calculator.check_sl_tp_hit(
        current_price=50500.0,
        direction="LONG",
        stop_loss=49000.0,
        take_profit=52000.0
    )
    assert result is None, "Should detect no hit"
    print(f"✅ No hit detected correctly: {result}")
    
    return True


def test_pnl_calculation():
    """Test P&L calculations"""
    print("\n" + "="*60)
    print("Test 3: P&L Calculation")
    print("="*60)
    
    calculator = PositionCalculator()
    
    # Test LONG win
    print("\n📊 Testing LONG winning trade...")
    result = calculator.calculate_pnl(
        entry_price=50000.0,
        exit_price=52000.0,
        position_size=1.0,
        direction="LONG"
    )
    print(f"   Entry: 50000.0 | Exit: 52000.0 | Size: 1.0")
    print(f"   P&L: {result['pnl']:+.2f} USDT ({result['pnl_percent']:+.2f}%)")
    assert result['pnl'] == 2000.0, "P&L should be +2000"
    assert result['pnl_percent'] == 4.0, "P&L% should be +4%"
    print("   ✅ Calculations correct")
    
    # Test LONG loss
    print("\n📊 Testing LONG losing trade...")
    result = calculator.calculate_pnl(
        entry_price=50000.0,
        exit_price=49000.0,
        position_size=1.0,
        direction="LONG"
    )
    print(f"   Entry: 50000.0 | Exit: 49000.0 | Size: 1.0")
    print(f"   P&L: {result['pnl']:+.2f} USDT ({result['pnl_percent']:+.2f}%)")
    assert result['pnl'] == -1000.0, "P&L should be -1000"
    assert result['pnl_percent'] == -2.0, "P&L% should be -2%"
    print("   ✅ Calculations correct")
    
    # Test SHORT win
    print("\n📊 Testing SHORT winning trade...")
    result = calculator.calculate_pnl(
        entry_price=3000.0,
        exit_price=2800.0,
        position_size=10.0,
        direction="SHORT"
    )
    print(f"   Entry: 3000.0 | Exit: 2800.0 | Size: 10.0")
    print(f"   P&L: {result['pnl']:+.2f} USDT ({result['pnl_percent']:+.2f}%)")
    assert result['pnl'] == 2000.0, "P&L should be +2000"
    print("   ✅ Calculations correct")
    
    # Test SHORT loss
    print("\n📊 Testing SHORT losing trade...")
    result = calculator.calculate_pnl(
        entry_price=3000.0,
        exit_price=3100.0,
        position_size=10.0,
        direction="SHORT"
    )
    print(f"   Entry: 3000.0 | Exit: 3100.0 | Size: 10.0")
    print(f"   P&L: {result['pnl']:+.2f} USDT ({result['pnl_percent']:+.2f}%)")
    assert result['pnl'] == -1000.0, "P&L should be -1000"
    print("   ✅ Calculations correct")
    
    return True


def test_risk_reward_ratio():
    """Test 1:2 Risk/Reward ratio"""
    print("\n" + "="*60)
    print("Test 4: Risk/Reward Ratio Validation")
    print("="*60)
    
    calculator = PositionCalculator(risk_percent=0.01, rr_ratio=2.0)
    
    # Calculate position
    result = calculator.calculate_position_with_price(
        symbol="BTCUSDT",
        direction="LONG",
        entry_price=50000.0,
        stop_loss=49000.0,
        equity=100000.0
    )
    
    if result:
        entry = result['entry_price']
        sl = result['stop_loss']
        tp = result['take_profit']
        
        risk_distance = abs(entry - sl)
        reward_distance = abs(tp - entry)
        rr_ratio = reward_distance / risk_distance if risk_distance > 0 else 0
        
        print(f"📊 Position Analysis:")
        print(f"   Entry: {entry:.2f}")
        print(f"   Stop Loss: {sl:.2f} (Risk: {risk_distance:.2f})")
        print(f"   Take Profit: {tp:.2f} (Reward: {reward_distance:.2f})")
        print(f"   R:R Ratio: 1:{rr_ratio:.1f}")
        
        assert rr_ratio == 2.0, f"R:R ratio should be 1:2, got 1:{rr_ratio}"
        print("   ✅ Risk/Reward ratio is correct (1:2)")
        
        return True
    else:
        print("❌ Position calculation failed")
        return False


def test_risk_management():
    """Test 1% risk per trade"""
    print("\n" + "="*60)
    print("Test 5: Risk Management (1% per trade)")
    print("="*60)
    
    calculator = PositionCalculator(risk_percent=0.01, rr_ratio=2.0)
    
    test_cases = [
        (100000.0, 1000.0, "100k equity"),
        (50000.0, 500.0, "50k equity"),
        (150000.0, 1500.0, "150k equity"),
    ]
    
    for equity, expected_risk, description in test_cases:
        print(f"\n📊 Testing {description}...")
        result = calculator.calculate_position_with_price(
            symbol="BTCUSDT",
            direction="LONG",
            entry_price=50000.0,
            stop_loss=49000.0,
            equity=equity
        )
        
        if result:
            risk = result['risk_amount']
            risk_percent = (risk / equity) * 100
            
            print(f"   Equity: {equity:.2f} USDT")
            print(f"   Risk Amount: {risk:.2f} USDT ({risk_percent:.1f}%)")
            
            assert risk == expected_risk, f"Risk should be {expected_risk}, got {risk}"
            assert risk_percent == 1.0, f"Risk should be 1%, got {risk_percent}%"
            print(f"   ✅ Risk is correctly 1% of equity")
        else:
            print(f"   ❌ Position calculation failed")
            return False
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Brain YAGATI v2 - Paper Trading Module Tests")
    print("="*60)
    
    tests = [
        ("Position Calculator", test_position_calculator),
        ("SL/TP Detection", test_sl_tp_checking),
        ("P&L Calculation", test_pnl_calculation),
        ("Risk/Reward Ratio", test_risk_reward_ratio),
        ("Risk Management", test_risk_management),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
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
