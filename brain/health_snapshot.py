"""
Health snapshot utilities for the Brain execution state.

This module provides pure, deterministic helpers to compute a lightweight
health snapshot from recent trade/activity data. It contains no business rules,
thresholds, or decision logic.
"""

from typing import Any, Dict, List

from brain_day.stats_utils import avg_rr, count_trades, win_loss_counts, win_rate

__all__ = ["compute_health_snapshot"]


def compute_health_snapshot(trades: List[Any]) -> Dict[str, Any]:
    """
    Compute a lightweight health snapshot from a list of trades.
    
    Args:
        trades: List of trade objects (dict or object with attributes)
        
    Returns:
        Dictionary containing trade metrics:
        - total_trades: Total number of trades
        - wins: Number of winning trades
        - losses: Number of losing trades
        - win_rate: Win rate as a float (0.0-1.0)
        - avg_rr: Average Risk-Reward ratio
        - has_activity: Whether there are any trades
    """
    if not trades:
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "avg_rr": 0.0,
            "has_activity": False,
        }

    total = count_trades(trades)
    wl = win_loss_counts(trades)
    w_rate = win_rate(trades)
    mean_rr = avg_rr(trades)

    wins = int(wl.get("wins", 0)) if isinstance(wl, dict) else 0
    losses = int(wl.get("losses", 0)) if isinstance(wl, dict) else 0

    return {
        "total_trades": int(total),
        "wins": wins,
        "losses": losses,
        "win_rate": float(w_rate),
        "avg_rr": float(mean_rr),
        "has_activity": bool(int(total) > 0),
    }
