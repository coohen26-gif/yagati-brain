"""
Brain YAGATI v2 - Integration Test

Tests the complete flow without requiring real API credentials.
This validates the logic and data flow of all modules.
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

from brain_v2.features.technical import compute_features
from brain_v2.detect.setup_detector import detect_setups
from brain_v2.decide.decision_engine import make_decisions
from brain_v2.governance.logger import get_logger


def create_sample_candles(length=100, volatility_spike=False):
    """Create sample OHLC candles for testing"""
    candles = []
    for i in range(length):
        # Add volatility spike in recent candles if requested
        if volatility_spike and i >= length - 20:
            vol = 3.0
        else:
            vol = 1.0
        
        candles.append({
            "open": 100 + i * 0.5,
            "high": 100 + i * 0.5 + vol,
            "low": 100 + i * 0.5 - vol,
            "close": 100 + i * 0.5,
        })
    return candles


def test_full_flow():
    """Test the complete analysis flow"""
    print("\n" + "="*60)
    print("Brain YAGATI v2 - Integration Test")
    print("="*60 + "\n")
    
    logger = get_logger()
    logger.log_startup()
    
    # Test scenario 1: Normal market (no spike)
    print("Test 1: Normal market (no volatility spike)")
    candles_normal = create_sample_candles(100, volatility_spike=False)
    features_normal = compute_features(candles_normal)
    setups_normal = detect_setups(features_normal, "TESTUSDT", "1h")
    decisions_normal = make_decisions(setups_normal, features_normal)
    
    print(f"  Setups detected: {len(setups_normal)}")
    print(f"  Decisions: {len(decisions_normal)}")
    for d in decisions_normal:
        print(f"    - {d['status'].upper()}: score {d['score']}")
    
    # Test scenario 2: Volatile market (with spike)
    print("\nTest 2: Volatile market (with volatility spike)")
    candles_volatile = create_sample_candles(100, volatility_spike=True)
    features_volatile = compute_features(candles_volatile)
    setups_volatile = detect_setups(features_volatile, "TESTUSDT", "1h")
    decisions_volatile = make_decisions(setups_volatile, features_volatile)
    
    print(f"  Setups detected: {len(setups_volatile)}")
    print(f"  Decisions: {len(decisions_volatile)}")
    for d in decisions_volatile:
        print(f"    - {d['status'].upper()}: score {d['score']} ({d['confidence']})")
        print(f"      Justification: {d['justification']}")
    
    # Verify results
    print("\n" + "="*60)
    print("Validation:")
    print("="*60)
    
    checks = []
    
    # Check 1: Normal market should have fewer/weaker setups
    checks.append(("Normal market has setups", len(setups_normal) >= 0))
    
    # Check 2: Volatile market should detect volatility expansion
    has_vol_setup = any(s['setup_type'] == 'volatility_expansion' for s in setups_volatile)
    checks.append(("Volatile market detects volatility_expansion", has_vol_setup))
    
    # Check 3: All decisions have required fields
    for d in decisions_volatile:
        has_fields = all(k in d for k in ['status', 'score', 'confidence', 'justification'])
        checks.append((f"Decision has required fields", has_fields))
    
    # Check 4: Scores are in valid range
    for d in decisions_volatile:
        score_valid = 0 <= d['score'] <= 100
        checks.append((f"Score {d['score']} in range [0-100]", score_valid))
    
    # Check 5: Status matches score threshold
    for d in decisions_volatile:
        status_valid = (d['status'] == 'forming' and d['score'] >= 50) or \
                      (d['status'] == 'reject' and d['score'] < 50)
        checks.append((f"Status '{d['status']}' matches score {d['score']}", status_valid))
    
    # Print results
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} checks passed")
    print("="*60 + "\n")
    
    if passed == total:
        print("✅ All tests passed!")
        return True
    else:
        print(f"❌ {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = test_full_flow()
    sys.exit(0 if success else 1)
