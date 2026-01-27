"""Manual validation of strategy scorer with existing diagnostic data."""

import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brain_core.strategy_scorer import score_strategies_from_diagnostics


def main():
    """Load existing strategy stats and compute scores."""
    
    # Load strategy_stats.json if it exists
    stats_path = 'strategy_stats.json'
    
    if not os.path.exists(stats_path):
        print(f"[WARNING] {stats_path} not found, using sample data")
        # Use sample data
        stats = [
            {
                'strategy_id': '27264511-cc45-4e19-aa6e-d5082a3cd834',
                'total': 8,
                'keep': 0,
                'adjust': 0,
                'reject': 1,
                'ignore': 7,
                'avg_rr': 0.585
            },
            {
                'strategy_id': 'ef3266ce-ed72-4035-afd8-ae2de99ef7cf',
                'total': 75,
                'keep': 6,
                'adjust': 1,
                'reject': 1,
                'ignore': 67,
                'avg_rr': 1.0434090909090907
            }
        ]
    else:
        print(f"[INFO] Loading {stats_path}")
        with open(stats_path, 'r') as f:
            stats = json.load(f)
    
    # Compute scores
    print(f"\n[INFO] Computing scores for {len(stats)} strategies...")
    results = score_strategies_from_diagnostics(stats)
    
    # Display results
    print("\n" + "="*80)
    print("STRATEGY SCORES (0-100 scale)")
    print("="*80)
    
    for result in results:
        print(f"\nStrategy ID: {result['strategy_id']}")
        print(f"  Score: {result['score']:.2f}")
        print(f"  Sample Size: {result['sample_size']} trades")
        print(f"  Breakdown:")
        for key, value in result['breakdown'].items():
            print(f"    {key}: {value}")
    
    print("\n" + "="*80)
    
    # Save to file
    output_path = 'strategy_scores_detailed.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[INFO] Detailed scores saved to {output_path}")


if __name__ == '__main__':
    main()
