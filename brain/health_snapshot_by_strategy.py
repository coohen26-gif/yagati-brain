"""
Strategy-grouped health snapshot utilities.

This module provides pure, deterministic helpers to compute health snapshots
grouped by strategy_id. It contains no business rules, thresholds, or decision logic.
"""

from typing import Any, Dict, List

from brain.health_snapshot import compute_health_snapshot

__all__ = ["compute_health_snapshot_by_strategy"]


def compute_health_snapshot_by_strategy(trades: List[Any]) -> Dict[str, Dict[str, Any]]:
    """
    Compute health snapshots grouped by strategy_id.
    
    Groups trades by their strategy_id (from dict key or object attribute).
    Trades with missing or empty strategy_id are grouped under "UNKNOWN".
    
    Args:
        trades: List of trade objects (dict or object with attributes)
        
    Returns:
        Dictionary mapping strategy_id to health snapshot metrics:
        {
            "<strategy_id>": {
                "total_trades": int,
                "wins": int,
                "losses": int,
                "win_rate": float,
                "avg_rr": float,
                "has_activity": bool
            }
        }
    """
    if not trades:
        return {}
    
    # Group trades by strategy_id
    grouped_trades: Dict[str, List[Any]] = {}
    
    for trade in trades:
        # Extract strategy_id from dict or object attribute
        strategy_id = None
        if isinstance(trade, dict):
            strategy_id = trade.get("strategy_id")
        else:
            strategy_id = getattr(trade, "strategy_id", None)
        
        # Use "UNKNOWN" for missing or empty strategy_id
        if not strategy_id:
            strategy_id = "UNKNOWN"
        
        if strategy_id not in grouped_trades:
            grouped_trades[strategy_id] = []
        
        grouped_trades[strategy_id].append(trade)
    
    # Compute health snapshot for each strategy
    result = {}
    for strategy_id, strategy_trades in grouped_trades.items():
        result[strategy_id] = compute_health_snapshot(strategy_trades)
    
    return result
