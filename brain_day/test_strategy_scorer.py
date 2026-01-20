"""Tests for strategy_scorer module.

This test suite validates the statistical methods and scoring functions
using known inputs and expected outputs.
"""

import sys
import os
import math

# Add parent directory to path to import brain_core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brain_core.strategy_scorer import (
    wilson_score_lower_bound,
    empirical_bayes_shrinkage,
    calculate_strategy_score,
    score_strategies_from_diagnostics
)


def test_wilson_score_basic():
    """Test Wilson score with known values."""
    # Test case 1: 7 wins, 3 losses (70% win rate, n=10)
    result = wilson_score_lower_bound(7, 3)
    assert 0.39 <= result <= 0.43, f"Expected ~0.40, got {result}"
    
    # Test case 2: 70 wins, 30 losses (70% win rate, n=100) - should be higher
    result_large = wilson_score_lower_bound(70, 30)
    assert 0.59 <= result_large <= 0.63, f"Expected ~0.61, got {result_large}"
    assert result_large > result, "Larger sample should give higher confidence"
    
    # Test case 3: No data
    result_zero = wilson_score_lower_bound(0, 0)
    assert result_zero == 0.0, f"Expected 0.0 for no data, got {result_zero}"
    
    # Test case 4: 100% win rate with small sample
    result_perfect = wilson_score_lower_bound(5, 0)
    assert 0.5 <= result_perfect <= 0.8, "Perfect WR should still be conservative with n=5"
    assert result_perfect < 1.0, "Should never return 1.0 for finite samples"
    
    print("✓ Wilson score basic tests passed")


def test_empirical_bayes_shrinkage_basic():
    """Test Empirical Bayes shrinkage."""
    # Test case 1: Small sample (5 trades) pulled toward prior
    result = empirical_bayes_shrinkage(
        observed_value=0.8,
        prior_mean=0.5,
        sample_size=5,
        shrinkage_strength=10
    )
    assert 0.55 <= result <= 0.65, f"Expected ~0.6, got {result}"
    assert result < 0.8, "Small sample should shrink toward prior"
    assert result > 0.5, "Should be between observed and prior"
    
    # Test case 2: Large sample (100 trades) stays close to observed
    result_large = empirical_bayes_shrinkage(
        observed_value=0.8,
        prior_mean=0.5,
        sample_size=100,
        shrinkage_strength=10
    )
    assert 0.75 <= result_large <= 0.80, f"Expected ~0.773, got {result_large}"
    assert result_large > result, "Large sample should shrink less"
    
    # Test case 3: Zero sample size defaults to prior
    result_zero = empirical_bayes_shrinkage(
        observed_value=0.8,
        prior_mean=0.5,
        sample_size=0,
        shrinkage_strength=10
    )
    assert result_zero == 0.5, "Zero sample should return prior"
    
    print("✓ Empirical Bayes shrinkage tests passed")


def test_calculate_strategy_score_basic():
    """Test strategy score calculation."""
    # Test case 1: Good strategy (70% WR, 1.2 avg RR, 10 trades)
    result = calculate_strategy_score(
        wins=7,
        losses=3,
        avg_rr=1.2
    )
    
    assert 'score' in result, "Result should have 'score' key"
    assert 'breakdown' in result, "Result should have 'breakdown' key"
    assert 'sample_size' in result, "Result should have 'sample_size' key"
    
    assert result['sample_size'] == 10, f"Expected 10 trades, got {result['sample_size']}"
    assert 0 <= result['score'] <= 100, f"Score should be in [0,100], got {result['score']}"
    assert 40 <= result['score'] <= 70, f"Expected score ~50-60, got {result['score']}"
    
    # Check breakdown components exist
    assert 'win_rate_raw' in result['breakdown']
    assert 'win_rate_wilson' in result['breakdown']
    assert 'win_rate_component' in result['breakdown']
    assert 'avg_rr_raw' in result['breakdown']
    assert 'avg_rr_shrunk' in result['breakdown']
    assert 'rr_component' in result['breakdown']
    assert 'volume_component' in result['breakdown']
    
    # Verify raw win rate
    assert abs(result['breakdown']['win_rate_raw'] - 0.7) < 0.01
    
    print("✓ Basic strategy score calculation tests passed")


def test_calculate_strategy_score_edge_cases():
    """Test edge cases for score calculation."""
    # Test case 1: No trades
    result_zero = calculate_strategy_score(
        wins=0,
        losses=0,
        avg_rr=0.0
    )
    assert result_zero['score'] == 0.0, "No trades should give score=0"
    assert result_zero['sample_size'] == 0
    
    # Test case 2: All losses
    result_losses = calculate_strategy_score(
        wins=0,
        losses=10,
        avg_rr=-1.0
    )
    assert result_losses['score'] < 30, "All losses should give low score"
    
    # Test case 3: All wins (should still be conservative with small sample)
    result_wins = calculate_strategy_score(
        wins=5,
        losses=0,
        avg_rr=2.0
    )
    assert 40 <= result_wins['score'] <= 80, "All wins with small sample should be moderate"
    
    # Test case 4: Large sample, high performance
    result_large = calculate_strategy_score(
        wins=80,
        losses=20,
        avg_rr=1.5
    )
    assert result_large['score'] > 70, "Large sample with good metrics should score high"
    
    print("✓ Edge case tests passed")


def test_score_monotonicity():
    """Test that scores increase with better metrics."""
    # Same trade count, increasing win rate
    score_30 = calculate_strategy_score(wins=3, losses=7, avg_rr=1.0)['score']
    score_50 = calculate_strategy_score(wins=5, losses=5, avg_rr=1.0)['score']
    score_70 = calculate_strategy_score(wins=7, losses=3, avg_rr=1.0)['score']
    
    assert score_30 < score_50 < score_70, "Score should increase with win rate"
    
    # Same win rate, increasing RR
    score_rr_low = calculate_strategy_score(wins=5, losses=5, avg_rr=0.5)['score']
    score_rr_mid = calculate_strategy_score(wins=5, losses=5, avg_rr=1.0)['score']
    score_rr_high = calculate_strategy_score(wins=5, losses=5, avg_rr=2.0)['score']
    
    assert score_rr_low < score_rr_mid < score_rr_high, "Score should increase with RR"
    
    # Same metrics, increasing sample size
    score_n5 = calculate_strategy_score(wins=3, losses=2, avg_rr=1.0)['score']
    score_n15 = calculate_strategy_score(wins=9, losses=6, avg_rr=1.0)['score']
    score_n50 = calculate_strategy_score(wins=30, losses=20, avg_rr=1.0)['score']
    
    assert score_n5 < score_n15 < score_n50, "Score should increase with sample size"
    
    print("✓ Monotonicity tests passed")


def test_score_strategies_from_diagnostics():
    """Test batch scoring from diagnostic format."""
    stats = [
        {
            'strategy_id': 'strategy_a',
            'wins': 7,
            'losses': 3,
            'avg_rr': 1.2
        },
        {
            'strategy_id': 'strategy_b',
            'wins': 2,
            'losses': 8,
            'avg_rr': 0.5
        },
        {
            'strategy_id': 'strategy_c',
            'wins': 15,
            'losses': 5,
            'avg_rr': 1.5
        }
    ]
    
    results = score_strategies_from_diagnostics(stats)
    
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    
    # Check all results have required fields
    for result in results:
        assert 'strategy_id' in result
        assert 'score' in result
        assert 'breakdown' in result
        assert 'sample_size' in result
        assert 0 <= result['score'] <= 100
    
    # Strategy C (best metrics) should score highest
    scores = {r['strategy_id']: r['score'] for r in results}
    assert scores['strategy_c'] > scores['strategy_a'], "Strategy C should outscore A"
    assert scores['strategy_a'] > scores['strategy_b'], "Strategy A should outscore B"
    
    print("✓ Batch scoring tests passed")


def test_score_strategies_alternate_naming():
    """Test batch scoring with 'keep'/'reject' naming."""
    stats = [
        {
            'strategy_id': 'strategy_x',
            'keep': 6,
            'reject': 4,
            'avg_rr': 1.1
        }
    ]
    
    results = score_strategies_from_diagnostics(stats)
    
    assert len(results) == 1
    assert results[0]['sample_size'] == 10
    assert results[0]['breakdown']['win_rate_raw'] == 0.6
    
    print("✓ Alternate naming tests passed")


def test_score_strategies_empty_input():
    """Test edge cases for batch scoring."""
    # Empty list
    results_empty = score_strategies_from_diagnostics([])
    assert results_empty == [], "Empty input should return empty list"
    
    # None input
    results_none = score_strategies_from_diagnostics(None)
    assert results_none == [], "None input should return empty list"
    
    # List with invalid entries
    stats_invalid = [
        None,
        {'strategy_id': 'valid', 'wins': 5, 'losses': 5, 'avg_rr': 1.0},
        "invalid",
        {'wins': 3, 'losses': 2}  # Missing strategy_id
    ]
    
    results_partial = score_strategies_from_diagnostics(stats_invalid)
    assert len(results_partial) == 1, "Should process only valid entries"
    assert results_partial[0]['strategy_id'] == 'valid'
    
    print("✓ Empty/invalid input tests passed")


def test_score_stability():
    """Test that scores are stable (small changes in input = small changes in output)."""
    base_score = calculate_strategy_score(wins=10, losses=10, avg_rr=1.0)['score']
    
    # Add one win
    score_plus_win = calculate_strategy_score(wins=11, losses=10, avg_rr=1.0)['score']
    delta_win = abs(score_plus_win - base_score)
    
    # Add one loss
    score_plus_loss = calculate_strategy_score(wins=10, losses=11, avg_rr=1.0)['score']
    delta_loss = abs(score_plus_loss - base_score)
    
    # Deltas should be small (< 5 points for 1 trade change out of 20)
    assert delta_win < 5, f"Score should change gradually, delta={delta_win}"
    assert delta_loss < 5, f"Score should change gradually, delta={delta_loss}"
    
    print("✓ Score stability tests passed")


def run_all_tests():
    """Run all test functions."""
    print("\n" + "="*60)
    print("Running Strategy Scorer Tests")
    print("="*60 + "\n")
    
    test_wilson_score_basic()
    test_empirical_bayes_shrinkage_basic()
    test_calculate_strategy_score_basic()
    test_calculate_strategy_score_edge_cases()
    test_score_monotonicity()
    test_score_strategies_from_diagnostics()
    test_score_strategies_alternate_naming()
    test_score_strategies_empty_input()
    test_score_stability()
    
    print("\n" + "="*60)
    print("All tests passed! ✓")
    print("="*60 + "\n")


if __name__ == '__main__':
    run_all_tests()
