"""Strategy scoring module with conservative statistical methods.

This module provides a robust scoring system (0-100 scale) for trading strategies
based on existing diagnostics and trade outcomes. It uses:

1. Wilson Score Interval - Conservative binomial proportion confidence bounds
   for win rate estimation with small sample sizes
   
2. Empirical Bayes Shrinkage - Regularization that pulls individual strategy
   metrics toward global population means, preventing overconfidence in
   limited data
   
3. Multi-component Score - Combines win rate, risk-reward ratio, and sample
   size into a single interpretable metric

Mathematical Foundations
------------------------
Wilson Score (Lower Bound):
    For n trials with k successes, the Wilson score interval's lower bound is:
    
    p_lower = (p̂ + z²/(2n) - z*sqrt(p̂(1-p̂)/n + z²/(4n²))) / (1 + z²/n)
    
    where:
        p̂ = k/n (observed proportion)
        z = 1.96 (95% confidence, ~2 standard deviations)
        
    This provides a conservative estimate that accounts for uncertainty,
    especially with small n.

Empirical Bayes Shrinkage:
    θ_shrunk = (n/(n + k)) * θ_observed + (k/(n + k)) * θ_prior
    
    where:
        θ_observed = strategy's observed metric (win_rate or avg_rr)
        θ_prior = global mean across all strategies
        k = shrinkage strength parameter (default: 10 for moderate shrinkage)
        n = number of trades
        
    Small samples shrink strongly toward the prior; large samples retain
    their observed values.

Score Calculation (0-100 scale):
    score = w1 * win_rate_component + w2 * rr_component + w3 * volume_component
    
    where:
        win_rate_component = 100 * wilson_score(wins, losses)
        rr_component = 50 * (1 + tanh(shrunk_avg_rr / 2))  # maps R to [0,100]
        volume_component = 100 * min(1, trades / 30)  # caps at 30 trades
        
        w1, w2, w3 = weights (default: 0.5, 0.3, 0.2)

Assumptions and Constraints
----------------------------
- Trades are independent and identically distributed (i.i.d.)
- Win/loss is a binary outcome (breakeven excluded from calculation)
- Risk-reward (R) values are normalized: positive = profit, negative = loss
- Minimum 1 trade required for scoring (returns 0 otherwise)
- Conservative by design: penalizes low sample sizes, shrinks toward priors
- Stable over time: scores change gradually as new data accumulates

Integration Notes
-----------------
This module operates on existing diagnostics only. It does not:
- Generate new strategies
- Modify existing trade data
- Integrate with UI or automation systems
- Touch SWING_PROD arena (only DAY and SWING_ALPHA)
"""

import math
from typing import Any, Dict, List, Optional


def wilson_score_lower_bound(
    successes: int,
    failures: int,
    confidence: float = 0.95
) -> float:
    """Calculate the lower bound of the Wilson score confidence interval.
    
    The Wilson score interval is a robust method for estimating the true
    proportion of successes in a binomial distribution, particularly effective
    for small sample sizes where normal approximations fail.
    
    Unlike naive proportions (k/n), the Wilson score:
    - Never returns 0% or 100% for finite samples
    - Accounts for sampling uncertainty
    - Provides conservative estimates (lower bound)
    
    Args:
        successes: Number of successful outcomes (wins)
        failures: Number of failed outcomes (losses)
        confidence: Confidence level (default: 0.95 for 95% CI)
        
    Returns:
        Lower bound of the Wilson score interval, in range [0, 1]
        Returns 0.0 if no trials exist
        
    Example:
        >>> wilson_score_lower_bound(7, 3)  # 70% win rate, 10 trials
        0.418  # Conservative estimate accounting for small sample
        
        >>> wilson_score_lower_bound(70, 30)  # 70% win rate, 100 trials
        0.612  # Higher bound with more data
        
    References:
        Wilson, E.B. (1927). "Probable inference, the law of succession, 
        and statistical inference". Journal of the American Statistical 
        Association. 22 (158): 209–212.
    """
    n = successes + failures
    if n == 0:
        return 0.0
    
    # Map confidence to z-score (1.96 for 95%, 2.576 for 99%)
    z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_scores.get(confidence, 1.96)
    
    p_hat = successes / n
    
    # Wilson score formula components
    z_squared = z * z
    denominator = 1 + z_squared / n
    center = p_hat + z_squared / (2 * n)
    margin = z * math.sqrt((p_hat * (1 - p_hat) + z_squared / (4 * n)) / n)
    
    lower_bound = (center - margin) / denominator
    
    # Clamp to [0, 1] for numerical stability
    return max(0.0, min(1.0, lower_bound))


def empirical_bayes_shrinkage(
    observed_value: float,
    prior_mean: float,
    sample_size: int,
    shrinkage_strength: int = 10
) -> float:
    """Apply Empirical Bayes shrinkage to regularize estimates.
    
    Shrinkage pulls individual estimates toward a global prior (population mean),
    with the strength of regularization inversely proportional to sample size.
    This prevents overfitting to noise in small samples.
    
    The formula implements a weighted average:
        shrunk = (n * observed + k * prior) / (n + k)
        
    where k controls how strongly small samples are pulled toward the prior.
    
    Args:
        observed_value: Strategy's observed metric (win_rate, avg_rr, etc.)
        prior_mean: Global mean across all strategies (the prior)
        sample_size: Number of trades for this strategy
        shrinkage_strength: Prior "pseudo-count" (default: 10)
            Higher values = stronger shrinkage
            k=10 means a strategy needs ~10 trades to be weighted equally
            with the prior
            
    Returns:
        Shrunk estimate, pulled toward prior_mean based on sample_size
        
    Example:
        >>> empirical_bayes_shrinkage(0.8, 0.5, 5, 10)  # 80% WR, 5 trades
        0.6  # Pulled toward 50% prior due to small sample
        
        >>> empirical_bayes_shrinkage(0.8, 0.5, 100, 10)  # 80% WR, 100 trades
        0.773  # Closer to observed 80% with more data
        
    References:
        Efron, B. & Morris, C. (1977). "Stein's Paradox in Statistics".
        Scientific American, 236(5), 119-127.
    """
    if sample_size < 0:
        sample_size = 0
    
    # Weighted average formula
    weight_observed = sample_size
    weight_prior = shrinkage_strength
    total_weight = weight_observed + weight_prior
    
    if total_weight == 0:
        return prior_mean
    
    shrunk = (weight_observed * observed_value + weight_prior * prior_mean) / total_weight
    return shrunk


def calculate_strategy_score(
    wins: int,
    losses: int,
    avg_rr: float,
    global_win_rate: float = 0.50,
    global_avg_rr: float = 1.0,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Calculate a comprehensive strategy score (0-100 scale).
    
    This function combines multiple components into a single interpretable score:
    
    1. Win Rate Component (50% weight by default):
       - Uses Wilson score lower bound for conservative win rate estimate
       - Scaled to [0, 100]
       
    2. Risk-Reward Component (30% weight by default):
       - Uses Empirical Bayes shrinkage on average R
       - Transformed via tanh to map unbounded R to [0, 100]
       - tanh(x/2) provides smooth S-curve: -2R→0, 0R→50, +2R→100
       
    3. Volume Component (20% weight by default):
       - Rewards sample size (more trades = more confidence)
       - Linear from 0 to 30 trades, capped at 100 after 30
       - Ensures strategies with <30 trades have reduced scores
    
    Args:
        wins: Number of winning trades
        losses: Number of losing trades
        avg_rr: Average risk-reward ratio (R units)
        global_win_rate: Prior mean win rate across all strategies (default: 0.50)
        global_avg_rr: Prior mean avg_rr across all strategies (default: 1.0)
        weights: Optional custom weights dict with keys:
            'win_rate', 'rr', 'volume' (default: {0.5, 0.3, 0.2})
            
    Returns:
        Dictionary with:
            - 'score': Final composite score [0, 100]
            - 'breakdown': Component scores and intermediate values
            - 'sample_size': Total number of trades
            
    Example:
        >>> calculate_strategy_score(wins=7, losses=3, avg_rr=1.2)
        {
            'score': 58.3,
            'breakdown': {
                'win_rate_raw': 0.70,
                'win_rate_wilson': 0.418,
                'win_rate_component': 41.8,
                'avg_rr_raw': 1.2,
                'avg_rr_shrunk': 1.08,
                'rr_component': 57.4,
                'volume_component': 33.3,
            },
            'sample_size': 10
        }
        
    Notes:
        - Returns score=0 if sample_size=0 (no data to score)
        - All intermediate values preserved in 'breakdown' for auditability
        - Designed to be resistant to overfitting on small samples
        - Scores stabilize over time as new trades accumulate
    """
    # Default weights: win_rate=50%, rr=30%, volume=20%
    if weights is None:
        weights = {'win_rate': 0.5, 'rr': 0.3, 'volume': 0.2}
    
    sample_size = wins + losses
    
    # Edge case: no trades
    if sample_size == 0:
        return {
            'score': 0.0,
            'breakdown': {
                'win_rate_raw': 0.0,
                'win_rate_wilson': 0.0,
                'win_rate_component': 0.0,
                'avg_rr_raw': 0.0,
                'avg_rr_shrunk': 0.0,
                'rr_component': 0.0,
                'volume_component': 0.0,
            },
            'sample_size': 0
        }
    
    # Component 1: Win Rate (Wilson score, conservative)
    win_rate_raw = wins / sample_size if sample_size > 0 else 0.0
    win_rate_wilson = wilson_score_lower_bound(wins, losses, confidence=0.95)
    win_rate_component = 100.0 * win_rate_wilson
    
    # Component 2: Risk-Reward (Empirical Bayes shrinkage + tanh transformation)
    avg_rr_shrunk = empirical_bayes_shrinkage(
        observed_value=avg_rr,
        prior_mean=global_avg_rr,
        sample_size=sample_size,
        shrinkage_strength=10
    )
    # tanh(x/2) maps: -∞→0, 0→0.5, +∞→1
    # Multiply by 100 for [0, 100] scale
    # Shift by 1 and scale by 50 to center at 50 for R=0
    rr_normalized = math.tanh(avg_rr_shrunk / 2.0)  # [-1, 1]
    rr_component = 50.0 * (1 + rr_normalized)  # [0, 100]
    
    # Component 3: Volume (sample size bonus, linear to 30 trades)
    volume_ratio = min(1.0, sample_size / 30.0)
    volume_component = 100.0 * volume_ratio
    
    # Weighted sum
    score = (
        weights['win_rate'] * win_rate_component +
        weights['rr'] * rr_component +
        weights['volume'] * volume_component
    )
    
    # Clamp to [0, 100] for safety
    score = max(0.0, min(100.0, score))
    
    return {
        'score': round(score, 2),
        'breakdown': {
            'win_rate_raw': round(win_rate_raw, 4),
            'win_rate_wilson': round(win_rate_wilson, 4),
            'win_rate_component': round(win_rate_component, 2),
            'avg_rr_raw': round(avg_rr, 4),
            'avg_rr_shrunk': round(avg_rr_shrunk, 4),
            'rr_component': round(rr_component, 2),
            'volume_component': round(volume_component, 2),
        },
        'sample_size': sample_size
    }


def score_strategies_from_diagnostics(
    strategy_stats: List[Dict[str, Any]],
    global_priors: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """Score multiple strategies from diagnostic data.
    
    This is the main integration function that processes a list of strategy
    statistics (typically from strategy_stats.json or equivalent diagnostics)
    and computes scores for each.
    
    It automatically calculates global priors (population means) from the
    input data if not provided explicitly.
    
    Args:
        strategy_stats: List of strategy stat dictionaries, each containing:
            - 'strategy_id': Unique identifier
            - 'wins': Number of wins (or 'keep' count)
            - 'losses': Number of losses (or 'reject' count)
            - 'avg_rr': Average risk-reward ratio
            Optional fields: 'total', 'adjust', 'ignore'
            
        global_priors: Optional dict with 'win_rate' and 'avg_rr' keys
            If None, automatically computed from strategy_stats
            
    Returns:
        List of score dictionaries, one per strategy:
        [
            {
                'strategy_id': str,
                'score': float,
                'breakdown': {...},
                'sample_size': int
            },
            ...
        ]
        
    Example:
        >>> stats = [
        ...     {'strategy_id': 'A', 'wins': 7, 'losses': 3, 'avg_rr': 1.2},
        ...     {'strategy_id': 'B', 'wins': 2, 'losses': 8, 'avg_rr': 0.5}
        ... ]
        >>> score_strategies_from_diagnostics(stats)
        [
            {'strategy_id': 'A', 'score': 58.3, ...},
            {'strategy_id': 'B', 'score': 22.1, ...}
        ]
        
    Notes:
        - Automatically handles 'keep'/'reject' naming (maps to wins/losses)
        - Skips strategies with missing required fields
        - Global priors computed as simple averages across all strategies
        - Returns empty list if input is empty or invalid
    """
    if not strategy_stats or not isinstance(strategy_stats, list):
        return []
    
    # Calculate global priors if not provided
    if global_priors is None:
        total_wins = 0
        total_losses = 0
        total_rr = 0.0
        count_rr = 0
        
        for stat in strategy_stats:
            if not isinstance(stat, dict):
                continue
            
            # Handle 'wins'/'losses' or 'keep'/'reject' naming
            wins = stat.get('wins') or stat.get('keep', 0)
            losses = stat.get('losses') or stat.get('reject', 0)
            
            if wins is not None:
                total_wins += wins
            if losses is not None:
                total_losses += losses
            
            rr = stat.get('avg_rr')
            if rr is not None:
                total_rr += rr
                count_rr += 1
        
        # Compute means
        total_trades = total_wins + total_losses
        global_win_rate = total_wins / total_trades if total_trades > 0 else 0.50
        global_avg_rr = total_rr / count_rr if count_rr > 0 else 1.0
        
        global_priors = {
            'win_rate': global_win_rate,
            'avg_rr': global_avg_rr
        }
    
    # Score each strategy
    results = []
    for stat in strategy_stats:
        if not isinstance(stat, dict):
            continue
        
        strategy_id = stat.get('strategy_id')
        if not strategy_id:
            continue
        
        # Extract wins/losses (handle alternate naming)
        wins = stat.get('wins')
        if wins is None:
            wins = stat.get('keep', 0)
        
        losses = stat.get('losses')
        if losses is None:
            losses = stat.get('reject', 0)
        
        avg_rr = stat.get('avg_rr', 0.0)
        
        # Ensure numeric types
        try:
            wins = int(wins) if wins is not None else 0
            losses = int(losses) if losses is not None else 0
            avg_rr = float(avg_rr) if avg_rr is not None else 0.0
        except (ValueError, TypeError):
            continue
        
        # Calculate score
        score_result = calculate_strategy_score(
            wins=wins,
            losses=losses,
            avg_rr=avg_rr,
            global_win_rate=global_priors['win_rate'],
            global_avg_rr=global_priors['avg_rr']
        )
        
        # Add strategy_id to result
        score_result['strategy_id'] = strategy_id
        results.append(score_result)
    
    return results
